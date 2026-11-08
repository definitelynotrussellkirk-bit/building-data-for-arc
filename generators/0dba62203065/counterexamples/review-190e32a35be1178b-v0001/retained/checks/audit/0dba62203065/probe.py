#!/usr/bin/env python3
"""Findings-only conditional-cycle audit; never edits selected source files."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
PACKET = HERE.parents[2]
REPO = PACKET / "repo"
TASK = "0dba62203065"
SOURCE = REPO / "generators" / TASK / "generator.py"
for folder in (REPO / "src", REPO / "shared" / "runtime"):
    sys.path.insert(0, str(folder))
spec = importlib.util.spec_from_file_location("audited_0dba62203065", SOURCE)
assert spec and spec.loader
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(value) -> bytes:
    return json.dumps(value, separators=(",", ":")).encode()


def components(grid):
    """Independent four-neighbor traversal of the selected body rectangle."""
    height, width = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(1, height) for c in range(width - 1) if grid[r][c]}
    found = []
    while unseen:
        first = min(unseen)
        unseen.remove(first)
        stack, cells = [first], []
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            for other in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if other in unseen:
                    unseen.remove(other)
                    stack.append(other)
        found.append(cells)
    return found


def conditional_cycle_rival(grid):
    """Read the actual header only when row 1 is occupied; infer it otherwise."""
    header = grid[0]
    if not any(grid[1]):
        start = header[0] - 2
        step = 1 if header[1] == 2 + (start + 1) % 7 else -1
        header = [2 + (start + step * c) % 7 for c in range(len(header))]
    out = deepcopy(grid)
    for cells in components(grid):
        color = header[min(c for _, c in cells)]
        for r, c in cells:
            out[r][c] = color
    return out


def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def main():
    canonical_path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    canonical = next(json.loads(line) for line in canonical_path.read_text().splitlines()
                     if json.loads(line).get("task_id") == TASK)
    pairs = canonical["train"] + canonical["test"]
    source_hash = digest(SOURCE.read_bytes())
    rule = canonical["program_solution"]
    base = gen.generate(77, 0, difficulty="medium")
    assert gen.observe_overrides(base)["body_origin"] == 2
    witness = deepcopy(base)
    anchors = {min(c for _, c in cells) for cells in components(base)}
    swap = None
    for anchor in sorted(anchors):
        if anchor < 2:
            continue
        for partner in range(2, len(base[0])):
            if partner in anchors or base[0][anchor] == base[0][partner]:
                continue
            candidate = deepcopy(base)
            candidate[0][anchor], candidate[0][partner] = candidate[0][partner], candidate[0][anchor]
            if gen.self_check(candidate) == [] and conditional_cycle_rival(candidate) != gen.rule_mirror(candidate):
                witness, swap = candidate, [anchor, partner]
                break
        if swap is not None:
            break
    assert swap is not None

    inputs = [witness] + [pair["input"] for pair in pairs]
    labels = [{"kind": "hand_mutated_generated_input", "label": "row_2_anchor_swap",
               "base_seed": 77, "base_sample_index": 0, "difficulty": "medium", "overrides": {},
               "mutation": {"swapped_header_columns_zero_based": swap},
               "self_check_errors": gen.self_check(witness),
               "documented_generator_domain": False,
               "domain_note": "Structural validator accepts it, and the written lookup rule applies, but SUMMARY.md and generate() require row-2 lessons to have cyclic headers."}]
    labels += [{"kind": "canonical", "index": i, "self_check_errors": gen.self_check(p["input"])} for i, p in enumerate(pairs)]
    seen = set()
    census = []
    for band_index, band in enumerate(("easy", "medium", "hard")):
        matched = valid = 0
        refuted = {name: 0 for name in gen.LESSON_COMPETITORS}
        local_seen = set()
        for index in range(100):
            seed = 700_000 + band_index * 10_000 + index
            grid = gen.generate(seed, index, difficulty=band)
            truth = gen.rule_mirror(grid)
            matched += conditional_cycle_rival(grid) == truth
            valid += gen.self_check(grid) == []
            grid_hash = digest(encoded(grid))
            seen.add(grid_hash)
            local_seen.add(grid_hash)
            for name, rival in gen.LESSON_COMPETITORS.items():
                refuted[name] += rival(grid) != truth
            if index < 2:
                inputs.append(grid)
                labels.append({"kind": "generated", "seed": seed, "sample_index": index,
                               "difficulty": band, "overrides": {}, "documented_generator_domain": True,
                               "self_check_errors": gen.self_check(grid)})
        census.append({"difficulty": band, "count": 100, "valid": valid,
                       "unique_inputs": len(local_seen), "conditional_rival_matches_python_mirror": matched,
                       "declared_lesson_competitor_refutations": refuted})

    report = {
        "schema": "audit-conditional-cycle-v1", "task_id": TASK,
        "finding_class": "reproduced_remaining_shortcut_with_out_of_generator_support_witness",
        "generator_sha256": source_hash, "rule_hash": gen.RULE_HASH,
        "canonical_program_solution_sha256": digest(rule.encode()),
        "canonical_record_sha256_compact_json": digest(encoded(canonical)),
        "prior_evidence_lead": "review-9e230aa538d1234f:v0001; notes.md explicitly records the row-1/non-cyclic coupling as a remaining limitation.",
        "prior_integrated_evidence_sha256": digest((SOURCE.parent / "evidence" / "review-review-9e230aa538d1234f-v0001.json").read_bytes()),
        "rival_description": "If body row 1 is blank, reconstruct the 2..8 cycle from header cells 0 and 1; otherwise read the actual header. Recolor each four-connected body component uniformly from its leftmost column.",
        "canonical": {
            "pairs": len(pairs),
            "conditional_rival_matches_known_outputs": sum(conditional_cycle_rival(p["input"]) == p["output"] for p in pairs),
            "declared_canonical_shortcuts_matches_known_outputs": {
                name: sum(rival(p["input"]) == p["output"] for p in pairs)
                for name, rival in gen.CANONICAL_SHORTCUTS.items()},
        },
        "census": {"sampler": "generate(seed=700000 + band_index*10000 + sample_index, sample_index=0..99, difficulty=easy|medium|hard, overrides={})",
                   "count": 300, "unique_inputs": len(seen), "bands": census,
                   "comparison_authority": "generator.rule_mirror; six generated samples plus all three canonical inputs and the witness are independently submitted to public Racket apply.",
                   "lesson_windows_checked": 0},
        "input_labels_in_order": labels,
        "witness": {"input_index": 0, "input_sha256_compact_json": digest(encoded(witness)),
                    "validator_errors": gen.self_check(witness), "dimensions": [len(witness), len(witness[0])],
                    "observed_overrides": gen.observe_overrides(witness), "legend_profile": gen.observe_legend_profile(witness),
                    "within_documented_generator_domain": False,
                    "outside_domain_reason": "The actual generator cannot emit an anchor-swap header when body_origin=2, even with the documented overrides.",
                    "rival_mirror_cell_differences": [
                        {"row": r, "column": c, "rival": conditional_cycle_rival(witness)[r][c], "python_mirror": gen.rule_mirror(witness)[r][c]}
                        for r in range(len(witness)) for c in range(len(witness[0]))
                        if conditional_cycle_rival(witness)[r][c] != gen.rule_mirror(witness)[r][c]]},
        "scope": "Source, summary, notes, tests, task-local probe, canonical record, and prior integrated evidence reviewed. No full battery, no source modifications. The raw Racket comparison is recorded separately after public apply.",
    }
    assert report["canonical"]["conditional_rival_matches_known_outputs"] == 3
    assert all(b["conditional_rival_matches_python_mirror"] == 100 for b in census)
    assert gen.self_check(witness) == []
    write("input.json", inputs)
    write("rival.json", [conditional_cycle_rival(grid) for grid in inputs])
    write("python_mirror.json", [gen.rule_mirror(grid) for grid in inputs])
    write("finding.json", report)
    print(json.dumps({"generator_sha256": source_hash, "canonical_fits": "3/3",
                      "generated_mirror_fits": "300/300", "unique_inputs": len(seen),
                      "witness_dimensions": report["witness"]["dimensions"], "swap": swap,
                      "public_apply_batch_size": len(inputs)}, indent=2))


if __name__ == "__main__":
    main()
