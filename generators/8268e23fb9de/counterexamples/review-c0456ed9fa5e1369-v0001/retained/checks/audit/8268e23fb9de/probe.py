"""Source-bound, findings-only audit; no repository edits or private runners."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
TASK = "8268e23fb9de"
SEED = 1
INDEX = 4
DIFFICULTY = "medium"
OVERRIDES = {}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, separators=(",", ":")) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("prepare", "finish"))
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    source = repo / "generators" / TASK / "generator.py"
    canonical = repo / "shared/data/canonical/puzzles.jsonl"
    base_record = repo / "shared/data/base/solutions/training/b7955b3c__8268e23fb9de.json"
    prelude = repo / "shared/runtime/arc_repl/racket_prelude/arc-prelude.rkt"

    if args.stage == "finish":
        evidence = json.loads((out / "counterexample.json").read_text())
        authority = json.loads((out / "racket.json").read_text())
        assert evidence["generator_sha256"] == sha(source), "Audited generator changed"
        assert evidence["canonical_file_sha256"] == sha(canonical), "Canonical file changed"
        assert authority["generator_sha256"] == evidence["generator_sha256"]
        assert authority["rule_hash_matches_catalog"] is True
        assert authority["executed_rule_hash"] == evidence["canonical_rule_hash"]
        assert len(authority["results"]) == 1
        result = authority["results"][0]
        assert result["input"] == evidence["input"]
        assert result["valid_output"] is True and result["error"] is None
        actual = result["output"]
        rival = evidence["rival_output"]
        differences = [
            {"row": r, "column": c, "actual_racket": value, "latent_topmost": rival[r][c]}
            for r, row in enumerate(actual) for c, value in enumerate(row)
            if value != rival[r][c]
        ]
        assert len(differences) == 5
        assert all(evidence["input"][d["row"]][d["column"]] == 8 for d in differences)
        evidence.update({
            "canonical_rule_hash": authority["executed_rule_hash"],
            "executed_callable_text_sha256": authority["rule_text_sha256"],
            "actual_racket_output": actual, "mismatches": differences,
            "generator_sha256_final": sha(source), "generator_unchanged": True,
            "canonical_file_sha256_final": sha(canonical), "canonical_unchanged": True,
            "input_sha256": result["input_sha256"], "output_sha256": result["output_sha256"],
            "public_cli_report": "racket.json", "status": "reproduced",
            "measured_count": {"generated_inputs_labelled_by_Racket": 1, "noise_cells": 5,
                               "noise_cells_mismatching_latent_draw": len(differences)},
            "finding": "The canonical rule calls (mode g), whose runtime helper removes color 0 before choosing a mode. The generator always paints semantic background 0. On this input 0 has 151 of 224 cells but the rule selects color 4 (46 nonzero cells). All five cyan restorations disagree with the actual pre-noise draw order. Guaranteeing a globally modal 0 alone would not repair this agreement defect.",
            "scope": "One fixed generated input checked through public Racket apply; no battery, frequency claim, or lesson-identifiability claim. Earlier current-source audit noted a background mismatch on an easy sample; this witness shows it persists with uniquely globally modal 0."
        })
        dump(out / "counterexample.json", evidence)
        verification = {"task_id": TASK, "generator_sha256": sha(source),
                        "generator_unchanged": True, "canonical_unchanged": True,
                        "canonical_rule_hash": authority["executed_rule_hash"],
                        "self_check": evidence["self_check"], "mismatches": differences,
                        "generated_inputs_labelled_by_Racket": 1,
                        "status": "reproduced semantic disagreement, not a semantic pass"}
        dump(out / "verification.json", verification)
        print(json.dumps(verification))
        return

    record = next(json.loads(line) for line in canonical.open()
                  if json.loads(line).get("task_id") == TASK)
    rule_text = record["program_solution"]
    rule_sha = hashlib.sha256(rule_text.encode()).hexdigest()
    dump(out / "canonical_record.json", {
        "task_id": TASK, "written_solution": record["written_solution"],
        "program_solution": rule_text, "canonical_file": str(canonical.relative_to(repo)),
        "canonical_file_sha256": sha(canonical), "program_source_sha256": rule_sha
    })

    sys.path.insert(0, str(repo / "shared/runtime"))
    spec = importlib.util.spec_from_file_location("audited_generator", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    direct = module.generate(SEED, INDEX, difficulty=DIFFICULTY, **OVERRIDES)
    draws = []
    clean = None
    original = module.draw_rect

    def record(grid, top, left, height, width, color):
        nonlocal clean
        result = original(grid, top, left, height, width, color)
        draws.append({"top": top, "left": left, "height": height, "width": width, "color": color})
        clean = [row[:] for row in grid]
        return result

    module.draw_rect = record
    try:
        grid = module.generate(SEED, INDEX, difficulty=DIFFICULTY, **OVERRIDES)
    finally:
        module.draw_rect = original
    assert grid == direct, "Instrumentation altered generated input"
    assert len(draws) == 3
    counts = Counter(value for row in grid for value in row)
    assert counts[0] > max(count for color, count in counts.items() if color != 0)
    colors = sorted(set(counts) - {0, 8})
    assert len(colors) == 3
    boxes = {}
    for color in colors:
        cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
        boxes[color] = [min(r for r, c in cells), min(c for r, c in cells),
                        max(r for r, c in cells), max(c for r, c in cells)]
    noise = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 8:
                candidates = [color for color, (top, left, bottom, right) in boxes.items()
                              if top <= r <= bottom and left <= c <= right]
                noise.append({"row": r, "column": c, "latent_topmost_color": clean[r][c],
                              "visible_bbox_candidates": candidates})
    checks = module.self_check(grid, difficulty=DIFFICULTY)
    assert checks == []
    evidence = {
        "schema": "source-bound-generator-audit-v1", "task_id": TASK,
        "classification": "reproduced generator-to-authority semantic mismatch",
        "generator_sha256": sha(source),
        "canonical_rule_hash": hashlib.sha256(" ".join(rule_text.split()).encode()).hexdigest()[:12],
        "canonical_program_source_sha256": rule_sha,
        "canonical_file": str(canonical.relative_to(repo)), "canonical_file_sha256": sha(canonical),
        "base_record_file": str(base_record.relative_to(repo)), "base_record_file_sha256": sha(base_record),
        "runtime_prelude_file": str(prelude.relative_to(repo)), "runtime_prelude_sha256": sha(prelude),
        "runtime_mode_definition": "(define (mode g [bg 0]) (define freq (color-frequency g)) (hash-remove! freq bg) (if (hash-empty? freq) bg (car (argmax cdr (hash->list freq)))))",
        "seed": SEED, "sample_index": INDEX, "difficulty": DIFFICULTY, "overrides": OVERRIDES,
        "input": grid, "actual_racket_output": None, "rival_output": clean,
        "rival_name": "generator_latent_topmost_restore",
        "rival_explanation": "Actual draw order before noise, retained by observing draw_rect calls; this is intended generator semantics, not an input-only solver.",
        "instrumentation_matches_uninstrumented_generate": grid == direct,
        "draw_order": draws, "color_counts": dict(counts), "global_mode": 0,
        "canonical_background_from_mode_helper": max((color for color in counts if color != 0), key=counts.get),
        "visible_rectangle_bboxes_inclusive": boxes, "noise_cells": noise,
        "self_check": checks,
        "domain_statement": "Unmodified generate(1, 4, difficulty='medium') with no overrides; 14x16, three visibly distinct overlapping rectangles, globally unique modal background 0, and five noise cells inside the latent covered area. Passes self_check and belongs to the default generated family. Canonical (mode g) excludes 0, violating the stated background role even on this globally 0-modal input.",
        "apply_command": {"cwd": "packet_root", "argv": ["python3", "review.py", "run", "python3", "-m", "arcpuzzles", "apply", TASK, "--input", "../checks/audit/8268e23fb9de/input.json", "--out", "../checks/audit/8268e23fb9de/racket.json"]},
        "replay_command": {"cwd": "packet_root", "argv": ["python3", "-B", "WORK/checks/audit/8268e23fb9de/probe.py", "prepare", "--repo", "WORK/repo", "--out", "WORK/checks/audit/8268e23fb9de"]},
        "status": "awaiting public Racket result"
    }
    dump(out / "input.json", grid)
    dump(out / "rival.json", clean)
    dump(out / "counterexample.json", evidence)
    print(json.dumps({"task_id": TASK, "seed": SEED, "sample_index": INDEX,
                      "generator_sha256": evidence["generator_sha256"],
                      "self_check": checks, "noise_cells": noise}))


if __name__ == "__main__":
    main()
