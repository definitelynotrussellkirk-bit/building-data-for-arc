#!/usr/bin/env python3
"""Focused, findings-only audit. Run from WORK/repo via run_with_racket.py.

Python transform results during candidate search are explicitly provisional.
The final audit consumes only outputs from public `arcpuzzles apply`.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs

TASK = "60baf0d49ed5"
ROOT = Path.cwd().resolve()
OUT = ROOT.parent / "checks" / "audit" / TASK
GEN = ROOT / "generators" / TASK / "generator.py"
OPS = ("rot90", "rot270", "rot180", "flip-h", "flip-v")


def load_generator():
    spec = importlib.util.spec_from_file_location("audit_generator_60baf0d49ed5", GEN)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def transform(g, op):
    if op == "rot90":
        return [list(row) for row in zip(*g[::-1])]
    if op == "rot270":
        return [list(row) for row in zip(*g)][::-1]
    if op == "rot180":
        return [row[::-1] for row in g[::-1]]
    if op == "flip-h":
        return [row[::-1] for row in g]
    return g[::-1]


def panels(g):
    side = len(g)
    return [[row[k * (side + 1):k * (side + 1) + side] for row in g] for k in range(3)]


def provisional_rule(g):
    a, b, c = panels(g)
    choices = [op for op in OPS if transform(a, op) == b]
    assert len(choices) == 1
    return transform(c, choices[0]), choices[0]


def rival(g):
    """Ignore panels A and B, always mirror panel C horizontally."""
    return transform(panels(g)[2], "flip-h")


def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n")


def prepare():
    m = load_generator()
    canonical = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    controls = []
    settings = [{}, {"n_distinct_colors": 1}, {"n_distinct_colors": 2},
                {"n_distinct_colors": 3}, {"palette_kind": "warm"},
                {"palette_kind": "cool"}, {"texture": "warm"}, {"texture": "cool"}]
    for overrides in settings:
        g = m.generate(0, 0, **overrides)
        controls.append({"seed": 0, "sample_index": 0, "difficulty": None,
                         "overrides": overrides, "input": g,
                         "self_check": m.self_check(g),
                         "motif_colors_excluding_background_and_dividers": sorted(set(v for row in g for v in row) - {0, 9}),
                         "all_colors": sorted(set(v for row in g for v in row))})
    assert all(case["input"] == controls[0]["input"] for case in controls)
    assert not any(case["self_check"] for case in controls)
    assert len(controls[1]["motif_colors_excluding_background_and_dividers"]) != 1

    # Bounded candidate search; these are Python-only hypotheses until apply.
    found = None
    checked_windows = 0
    unique_inputs = set()
    for seed in range(256):
        grids = [m.generate(seed, i) for i in range(4)]
        unique_inputs.update(json.dumps(g, separators=(",", ":")) for g in grids)
        assert all(not m.self_check(g) for g in grids)
        predictions = [provisional_rule(g) for g in grids]
        checked_windows += 1
        if all(rival(g) == output for g, (output, op) in zip(grids[:3], predictions[:3])) and rival(grids[3]) != predictions[3][0]:
            found = {"seed": seed, "sample_indices": list(range(4)), "difficulty": None,
                     "overrides": {}, "inputs": grids,
                     "provisional_operations": [op for output, op in predictions]}
            break
    assert found is not None, "No fixed-horizontal-flip witness within stated search bound"
    # Check that this is an actual default production lesson, with the public API.
    episodes = Catalog(ROOT).generate(TASK, count=1, seed=found["seed"], allow_unapproved=True)
    assert len(episodes) == 1
    episode = episodes[0]
    assert len(episode["train"]) == 3 and len(episode["test"]) == 1
    assert [p["input"] for p in episode["train"] + episode["test"]] == found["inputs"]
    write("production.json", episode)

    items = []
    for pair in canonical:
        items.append({"id": f"canonical-{pair['split']}-{pair['pair_index']}",
                      "origin": "canonical", **pair, "self_check": m.self_check(pair["input"])})
    items.append({"id": "ignored-controls-seed0-index0", "origin": "generated",
                  **controls[1], "documented_domain": True})
    for index, g in enumerate(found["inputs"]):
        items.append({"id": f"production-{index}", "origin": "generated", "input": g,
                      "seed": found["seed"], "sample_index": index, "difficulty": None,
                      "overrides": {}, "self_check": m.self_check(g), "documented_domain": True,
                      "split": "train" if index < 3 else "test"})
    write("input.json", [item["input"] for item in items])
    write("probe.json", {"task_id": TASK, "generator_sha256": hashlib.sha256(GEN.read_bytes()).hexdigest(),
                         "version": m.VERSION, "axes": m.AXES,
                         "rival_description": rival.__doc__, "controls": controls,
                         "candidate_search": {"method": "Python-only provisional rule, fixed horizontal mirror rival; then verify selected witness with public apply",
                                              "seed_range_inclusive": [0, checked_windows - 1], "sample_indices": [0, 1, 2, 3],
                                              "windows_checked": checked_windows, "unique_generated_inputs_checked": len(unique_inputs)},
                         "production": found, "apply_items": items})
    print(json.dumps({"prepared": True, "witness_seed": found["seed"], "search_windows": checked_windows,
                      "public_apply_inputs": len(items), "control_colors": controls[1]["all_colors"]}))


def finish():
    m = load_generator()
    meta = json.loads((OUT / "probe.json").read_text())
    applied = json.loads((OUT / "racket.json").read_text())
    assert applied["generator_sha256"] == meta["generator_sha256"]
    assert hashlib.sha256(GEN.read_bytes()).hexdigest() == meta["generator_sha256"]
    assert applied["rule_hash_matches_catalog"] is True
    for case in meta["controls"]:
        assert m.generate(case["seed"], case["sample_index"], **case["overrides"]) == case["input"]
    # Verify the stated unique-input denominator, not just the call count.
    first_seed, last_seed = meta["candidate_search"]["seed_range_inclusive"]
    unique_inputs = {json.dumps(m.generate(seed, i), separators=(",", ":"))
                     for seed in range(first_seed, last_seed + 1) for i in range(4)}
    assert len(unique_inputs) == meta["candidate_search"]["unique_generated_inputs_checked"]
    rows = []
    for item, result in zip(meta["apply_items"], applied["results"], strict=True):
        assert result["input"] == item["input"]
        assert result["output"] is not None, result
        assert result["valid_output"] is True and result["error"] is None
        assert result["generator_domain"] == {"status": "valid", "errors": []}
        assert not m.self_check(item["input"]), item["id"]
        if item["origin"] == "canonical":
            assert result["output"] == item["output"]
        predicted = rival(item["input"])
        rows.append({"id": item["id"], "input": item["input"], "racket_output": result["output"],
                     "rival_output": predicted, "rival_matches_racket": predicted == result["output"],
                     "self_check": [], "documented_domain": True,
                     "seed": item.get("seed"), "sample_index": item.get("sample_index"),
                     "overrides": item.get("overrides"), "split": item.get("split")})
    canonical = [row for row in rows if row["id"].startswith("canonical-")]
    production = [row for row in rows if row["id"].startswith("production-")]
    assert [row["rival_matches_racket"] for row in canonical] == [True, True, False]
    assert [row["rival_matches_racket"] for row in production] == [True, True, True, False]
    episode = json.loads((OUT / "production.json").read_text())
    assert [p["output"] for p in episode["train"] + episode["test"]] == [row["racket_output"] for row in production]
    report = {"task_id": TASK, "generator_sha256": applied["generator_sha256"],
              "rule_text_sha256": applied["rule_text_sha256"], "executed_rule_hash": applied["executed_rule_hash"],
              "catalog_rule_hash": applied["catalog_rule_hash"], "rule_hash_matches_catalog": True,
              "findings": [{"id": "A60-1", "kind": "reproduced exact-control defect",
                             "summary": "n_distinct_colors=1,2,3 and warm/cool palette_kind or texture overrides produce the identical seed=0 sample_index=0 grid. n_distinct_colors=1 emits two motif colors, plus 0 and 9."},
                            {"id": "A60-2", "kind": "reproduced lesson shortcut",
                             "summary": "Always mirror panel C horizontally fits both canonical demonstrations but fails the canonical query. It also fits all three demonstrations in a public default production lesson and fails that lesson's query.",
                             "production_seed": meta["production"]["seed"], "n_train": 3, "n_test": 1,
                             "production_policy": "public Catalog.generate default, three ordered demonstrations at indices 0..2 and query at index 3",
                             "query_rotations": "unknown; not evaluated"}],
              "counts": {"public_apply_inputs": len(rows), "public_apply_outputs_present": len(rows),
                         "canonical_rival_demo_matches": 2, "canonical_demo_count": 2,
                         "canonical_query_disagreements": 1, "canonical_query_count": 1,
                         "production_rival_demo_matches": 3, "production_demo_count": 3,
                         "production_query_disagreements": 1, "production_query_count": 1},
              "candidate_search": meta["candidate_search"], "cases": rows,
              "limitations": ["Focused audit; no full battery, broad distribution census, or query rotations.",
                              "A lesson shortcut is observed ambiguity against this named rival; labels themselves are correct.",
                              "Control equality observed for the eight declared-control calls at seed 0/index 0, not a frequency estimate.",
                              "No selected generator, reference, or shared-runtime files were edited."]}
    write("findings.json", report)
    print(json.dumps({"audit": "complete", "findings": [f["id"] for f in report["findings"]],
                      "racket_verified_inputs": len(rows), "generator_sha256": report["generator_sha256"],
                      "rule_text_sha256": report["rule_text_sha256"]}))


if __name__ == "__main__":
    {"prepare": prepare, "finish": finish}[sys.argv[1]]()
