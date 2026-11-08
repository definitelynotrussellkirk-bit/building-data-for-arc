"""Read-only task audit; the Python rival is an intentional rule ablation.

Run through packet review.py run. prepare materializes inputs; analyze consumes
outputs from the public Racket apply command. No Python result is called truth.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK = "1594f141732b"
HERE = Path(__file__).resolve().parent


def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            cells = [(r, c)]
            seen.add((r, c))
            for rr, cc in cells:
                for nr, nc in ((rr-1, cc), (rr+1, cc), (rr, cc-1), (rr, cc+1)):
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        cells.append((nr, nc))
            bbox = (min(p[0] for p in cells), min(p[1] for p in cells),
                    max(p[0] for p in cells), max(p[1] for p in cells))
            out.append((color, cells, bbox))
    return out


def loose_bbox_cross(grid, *, force_red=False):
    """Ablate only exact-outline recognition; retain 4-connectivity/singletons."""
    objs = components(grid)
    dots = [cells[0] for color, cells, _ in objs if color == 2 and len(cells) == 1]
    out = [row[:] for row in grid]
    for color, _, (r1, c1, r2, c2) in objs:
        if color == 2 or r2 - r1 < 2 or c2 - c1 < 2:
            continue
        paint = 2 if force_red else color
        for dr, dc in dots:
            if r1 < dr < r2 and c1 < dc < c2:
                for c in range(c1 + 1, c2):
                    out[dr][c] = paint
                for r in range(r1 + 1, r2):
                    out[r][dc] = paint
    return out


def prepare():
    root = find_root(__file__)
    gen, source, source_sha = load_selected_generator(TASK, root=root)
    canonical = canonical_pairs(TASK, root=root)
    row_bytes = next(line.rstrip(b"\r\n") for line in canonical_path(root).read_bytes().splitlines()
                     if json.loads(line).get("task_id") == TASK)
    rule = json.loads(row_bytes)["program_solution"]
    inputs, recipes = [], []
    for pair in canonical:
        inputs.append(pair["input"])
        recipes.append({"kind": "canonical", "variant": pair["variant"],
                        "split": pair["split"], "pair_index": pair["pair_index"],
                        "stored_output": pair["output"],
                        "self_check": gen.self_check(pair["input"])})
    for difficulty in ("easy", "medium", "hard"):
        for seed in (0, 1, 17):
            for sample_index in range(6):
                grid = gen.generate(seed, sample_index, difficulty=difficulty)
                inputs.append(grid)
                recipes.append({"kind": "generated", "difficulty": difficulty,
                                "seed": seed, "sample_index": sample_index,
                                "overrides": {}, "self_check": gen.self_check(grid)})
    for texture in gen.DEGENERATE_TEXTURES:
        grid = gen.generate(0, 0, texture=texture)
        inputs.append(grid)
        recipes.append({"kind": "documented_degenerate", "seed": 0, "sample_index": 0,
                        "overrides": {"texture": texture},
                        "self_check_default": gen.self_check(grid),
                        "self_check": gen.self_check(grid, meta={"texture": texture})})
    assert len(inputs) <= 64
    save("input.json", inputs)
    save("recipes.json", recipes)
    binding = {"task_id": TASK, "version": gen.VERSION,
               "source_path": str(source.relative_to(root)), "generator_sha256": source_sha,
               "canonical_path": str(canonical_path(root).relative_to(root)),
               "canonical_row_sha256_excluding_newline": digest(row_bytes),
               "rule_sha256_program_solution_utf8": digest(rule.encode()),
               "input_sha256": digest((HERE / "input.json").read_bytes()),
               "population": dict(Counter(recipe["kind"] for recipe in recipes)),
               "tests_present": (source.parent / "tests").is_dir(),
               "review_index_present": (source.parent / "evidence/review_index.json").exists(),
               "core_semantic_hooks_present": [name for name in
                   ("strict_canonical_like", "SEMANTIC_WITNESSES", "lesson_identifiable")
                   if hasattr(gen, name)]}
    save("source-binding.json", binding)
    print(json.dumps(binding, sort_keys=True))


def analyze():
    inputs = json.loads((HERE / "input.json").read_text())
    recipes = json.loads((HERE / "recipes.json").read_text())
    receipt = json.loads((HERE / "racket.json").read_text())
    print("Racket receipt top-level keys:", sorted(receipt) if isinstance(receipt, dict) else "list")
    if not isinstance(receipt, dict) or receipt.get("schema") != "arcpuzzles-apply-v1":
        raise ValueError("Inspect the public apply receipt schema before consuming it")
    results = receipt["results"]
    assert all(result["valid_output"] and result["error"] is None for result in results)
    outputs = [result["output"] for result in results]
    assert len(outputs) == len(inputs)
    assert [result["input"] for result in results] == inputs
    binding = json.loads((HERE / "source-binding.json").read_text())
    assert receipt["generator_sha256"] == binding["generator_sha256"]
    assert receipt["executed_rule_hash"] == binding["rule_sha256_program_solution_utf8"][:12]
    assert receipt["rule_hash_matches_catalog"] is True
    totals = {}
    examples = []
    for i, (grid, actual, recipe) in enumerate(zip(inputs, outputs, recipes)):
        if isinstance(actual, dict):
            actual = actual["output"]
        rival = loose_bbox_cross(grid)
        red_rival = loose_bbox_cross(grid, force_red=True)
        kind = recipe["kind"]
        counters = totals.setdefault(kind, Counter())
        counters["checked"] += 1
        counters["validator_pass"] += not recipe["self_check"]
        counters["loose_bbox_agrees"] += rival == actual
        counters["red_cross_agrees"] += red_rival == actual
        counters["output_red_cells"] += sum(v == 2 for row in actual for v in row)
        if kind == "generated":
            objs = components(grid)
            red_cells = [cells[0] for color, cells, _ in objs if color == 2 and len(cells) == 1]
            dot_counts = [sum(r1 < r < r2 and c1 < c < c2 for r, c in red_cells)
                          for color, _, (r1, c1, r2, c2) in objs if color != 2]
            counters["has_multi_dot_frame"] += any(n > 1 for n in dot_counts)
            counters["frames"] += len(dot_counts)
        if "stored_output" in recipe:
            counters["stored_output_agrees"] += recipe["stored_output"] == actual
        if rival != actual:
            differences = [{"row": r, "column": c, "input": grid[r][c],
                            "racket": actual[r][c], "rival": rival[r][c]}
                           for r in range(len(grid)) for c in range(len(grid[0]))
                           if rival[r][c] != actual[r][c]]
            examples.append({"input_index": i, "recipe": recipe, "input": grid,
                             "racket_output": actual, "loose_bbox_output": rival,
                             "differences": differences})
    save("witnesses.json", examples)
    summary = {"population_results": totals, "witness_count": len(examples),
               "generator_sha256": receipt["generator_sha256"],
               "canonical_rule_sha256": binding["rule_sha256_program_solution_utf8"],
               "executed_rule_text_sha256": receipt["rule_text_sha256"],
               "all_racket_outputs_valid": True,
               "racket_receipt_sha256": digest((HERE / "racket.json").read_bytes()),
               "witness_domain": "Canonical labeled train[1] and test[0]; not validator-only.",
               "lesson_claim": "Generated-support equivalence for this explicit rival; no empirical whole-lesson census."}
    save("probe-summary.json", summary)
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "analyze"))
    args = parser.parse_args()
    (prepare if args.mode == "prepare" else analyze)()
