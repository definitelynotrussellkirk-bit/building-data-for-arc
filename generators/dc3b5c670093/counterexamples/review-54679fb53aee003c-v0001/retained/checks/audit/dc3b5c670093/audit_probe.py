"""Find and verify teaching ambiguities in the unchanged assigned audit target.

This deliberately implements rivals for evidence only. It never edits a
generator or reference rule and never imports private runner functions.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REPO = ROOT / "repo"
TASK = "dc3b5c670093"
GEN = REPO / "generators" / TASK / "generator.py"
LEDGER = REPO / "shared/data/canonical/puzzles.jsonl"


def digest(value):
    return hashlib.sha256(value).hexdigest()


def grid_key(grid):
    return json.dumps(grid, separators=(",", ":"))


def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def load_generator():
    spec = importlib.util.spec_from_file_location("audit_target_dc3b", GEN)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def render(grid, rival=None):
    h, w = len(grid), len(grid[0])
    tr = min(r for r, row in enumerate(grid) if any(row))
    template = [grid[tr][:2], grid[tr + 1][:2]]
    out = [[0] * w for _ in range(h)]
    col, scale = 0, 1
    while col < w:
        pivot = h // 2 - 1 if rival == "canvas_center" and scale > 1 else tr
        top, bottom = pivot + 1 - scale, pivot + scale
        if rival == "complete_width" and col + 2 * scale > w:
            break
        if rival == "complete_rectangle" and (
            col + 2 * scale > w or top < 0 or bottom >= h
        ):
            break
        for r in range(max(0, top), min(h, bottom + 1)):
            for c in range(col, min(w, col + 2 * scale)):
                out[r][c] = template[int(r > pivot)][int(c - col >= scale)]
        col += 2 * scale
        scale *= 2
    return out


RIVALS = {
    "canvas_center": "Keep the given template; vertically center every enlarged copy on the canvas.",
    "complete_width": "Double the 2x2 template rightward, stopping before a block would cross the right border.",
    "complete_rectangle": "Double the 2x2 template rightward, stopping before a block would cross any canvas border.",
}


def prepare():
    module = load_generator()
    rows = [json.loads(line) for line in LEDGER.read_text().splitlines()
            if json.loads(line).get("task_id") == TASK]
    canonical = []
    rules = set()
    row_hashes = []
    for record in rows:
        rules.add(record["program_solution"])
        row_hashes.append({"source": record["source"],
                           "record_json_sha256": digest(json.dumps(record, sort_keys=True).encode())})
        for split in ("train", "test"):
            for index, pair in enumerate(record.get(split, [])):
                canonical.append({"source": record["source"], "split": split,
                                  "pair_index": index, **pair})
    assert len(rules) == 1
    program = next(iter(rules))
    episodes = [json.loads(line) for line in (HERE / "episodes.jsonl").read_text().splitlines()]
    source_hash = digest(GEN.read_bytes())
    assert all(ep["provenance"]["generator_sha256"] == source_hash for ep in episodes)
    assert all(ep["provenance"]["rule_hash"] == module.RULE_HASH for ep in episodes)
    assert all(ep["provenance"]["overrides"] == {} for ep in episodes)
    pairs = [pair for ep in episodes for split in ("train", "test") for pair in ep[split]]
    checks = {
        "generator_sha256": source_hash,
        "generator_version": module.VERSION,
        "catalog_rule_hash": module.RULE_HASH,
        "canonical_program_text_sha256": digest(program.encode()),
        "canonical_record_hashes": row_hashes,
        "canonical_pair_positions": len(canonical),
        "unique_canonical_pairs": len({grid_key([p["input"], p["output"]]) for p in canonical}),
        "canonical_reference_formula_matches": sum(render(p["input"]) == p["output"] for p in canonical),
        "production_sampler": "arcpuzzles generate, original split order, 3 demonstrations / 1 query",
        "phase": "audit_unchanged_target",
        "seed_range_inclusive": [episodes[0]["seed"], episodes[-1]["seed"]],
        "sample_indices_by_seed": {str(ep["seed"]): ep["sample_indices"] for ep in episodes},
        "difficulty": "hard",
        "overrides": {},
        "lesson_count": len(episodes),
        "pair_count": len(pairs),
        "unique_generated_inputs": len({grid_key(p["input"]) for p in pairs}),
        "generator_rejections": [item for ep in episodes for item in ep["rejections"]],
        "validator_pass_count": sum(module.self_check(p["input"]) == [] for p in pairs),
        "reference_formula_match_count": sum(render(p["input"]) == p["output"] for p in pairs),
        "declared_canonical_shortcuts": list(getattr(module, "CANONICAL_SHORTCUTS", ())),
        "declared_lesson_competitors": list(getattr(module, "LESSON_COMPETITORS", ())),
        "auditor_rivals": {},
    }
    witness_candidates = {}
    for name, description in RIVALS.items():
        canonical_fits = sum(render(p["input"], name) == p["output"] for p in canonical)
        ambiguous = []
        for ep in episodes:
            if all(render(p["input"], name) == p["output"] for p in ep["train"]) and any(
                render(p["input"], name) != p["output"] for p in ep["test"]
            ):
                ambiguous.append(ep["seed"])
        checks["auditor_rivals"][name] = {
            "description": description,
            "canonical_fits": canonical_fits,
            "canonical_denominator": len(canonical),
            "query_ambiguity_lesson_count": len(ambiguous),
            "lesson_denominator": len(episodes),
            "ambiguous_episode_seeds": ambiguous,
        }
        if canonical_fits == len(canonical) and ambiguous:
            witness_candidates[name] = ambiguous
    assert witness_candidates, "No ambiguity in sampled lessons; preserve sample and report no witness."
    selected = max(witness_candidates, key=lambda key: len(witness_candidates[key]))
    seed = witness_candidates[selected][0]
    episode = next(ep for ep in episodes if ep["seed"] == seed)
    witness_pairs = []
    for split in ("train", "test"):
        for index, pair in enumerate(episode[split]):
            accepted = next(row for row in episode["sampling"]["accepted_pairs"]
                            if row["split"] == split and row["pair_index"] == index)
            witness_pairs.append({
                "split": split, "pair_index": index,
                "sample_index": accepted["sample_index"],
                "validator_errors": module.self_check(pair["input"]),
                "documented_generator_domain": True,
                "domain_basis": "Unmodified production generation, no overrides; target self_check passes.",
                "observed_axes": module.observe_overrides(pair["input"]),
                "input": pair["input"],
                "generation_racket_output": pair["output"],
                "rival_output": render(pair["input"], selected),
            })
    witness = {
        "task_id": TASK, "classification": "reproduced teaching defect",
        "generator_sha256": source_hash,
        "generator_version": module.VERSION,
        "catalog_rule_hash": module.RULE_HASH,
        "canonical_program_text_sha256": checks["canonical_program_text_sha256"],
        "seed": seed, "difficulty": "hard", "overrides": {},
        "sample_indices": episode["sample_indices"],
        "lesson_assembly": "Production CLI default order, samples 0..2 demonstrations and sample 3 query; no rotation.",
        "rival": selected, "rival_description": RIVALS[selected],
        "pairs": witness_pairs,
        "canonical_source_pair_fit": checks["auditor_rivals"][selected]["canonical_fits"],
        "canonical_pair_denominator": len(canonical),
        "apply_input_order": [{"type": "canonical", "source": p["source"], "split": p["split"],
                               "pair_index": p["pair_index"]} for p in canonical] +
                             [{"type": "witness", "split": p["split"], "pair_index": p["pair_index"]}
                              for p in witness_pairs],
    }
    save("summary.json", checks)
    save("witness.json", witness)
    save("witness_episode.json", episode)
    save("input.json", [p["input"] for p in canonical] + [p["input"] for p in witness_pairs])
    print(json.dumps({"selected_rival": selected, "seed": seed,
                      "counts": checks["auditor_rivals"]}, indent=2))


def finalize():
    witness = json.loads((HERE / "witness.json").read_text())
    receipt = json.loads((HERE / "racket.json").read_text())
    print(json.dumps({key: value for key, value in receipt.items() if key != "results"}, indent=2))
    assert receipt["generator_sha256"] == witness["generator_sha256"]
    assert receipt["rule_hash_matches_catalog"] is True
    assert all(result["error"] is None for result in receipt["results"])
    results = receipt["results"]
    offset = witness["canonical_pair_denominator"]
    for pair, result in zip(witness["pairs"], results[offset:]):
        actual = result["output"]
        assert actual == pair["generation_racket_output"]
        pair["actual_racket_output"] = actual
        pair["rival_matches_actual"] = pair["rival_output"] == actual
        pair["differing_cells"] = [
            {"row": r, "column": c, "actual": actual[r][c], "rival": pair["rival_output"][r][c]}
            for r in range(len(actual)) for c in range(len(actual[0]))
            if actual[r][c] != pair["rival_output"][r][c]
        ]
    inputs = json.loads((HERE / "input.json").read_text())
    witness["actual_racket_canonical_fit_count"] = sum(
        render(grid, witness["rival"]) == result["output"]
        for grid, result in zip(inputs[:offset], results[:offset])
    )
    assert witness["actual_racket_canonical_fit_count"] == offset
    assert all(p["rival_matches_actual"] for p in witness["pairs"] if p["split"] == "train")
    assert all(not p["rival_matches_actual"] for p in witness["pairs"] if p["split"] == "test")
    witness["executed_rule_hash"] = receipt["executed_rule_hash"]
    witness["rule_hash_matches_catalog"] = receipt["rule_hash_matches_catalog"]
    witness["apply_receipt"] = "checks/audit/dc3b5c670093/racket.json"
    witness["commands_record"] = "checks/audit/dc3b5c670093/commands.json"
    witness["apply_command"] = next(record for record in json.loads((HERE / "commands.json").read_text())
                                    if "apply" in record["argv"])
    save("witness.json", witness)
    print(json.dumps({"verified": True, "rival": witness["rival"], "seed": witness["seed"],
                      "query_differing_cells": len(witness["pairs"][-1]["differing_cells"])}))


if __name__ == "__main__":
    {"prepare": prepare, "finalize": finalize}[sys.argv[1]]()
