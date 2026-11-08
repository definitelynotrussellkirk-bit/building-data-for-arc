"""Bounded, source-bound cc100a8ad437 audit; public helpers and CLI only.

Run from the outer packet folder:
  WORK/.venv/bin/python3 WORK/checks/audit/cc100a8ad437/probe.py prepare
  WORK/.venv/bin/python3 review.py run ../.venv/bin/python3 -m arcpuzzles apply cc100a8ad437 --input ../checks/audit/cc100a8ad437/input.json --check-generator-domain --out ../checks/audit/cc100a8ad437/racket.json
  WORK/.venv/bin/python3 WORK/checks/audit/cc100a8ad437/probe.py analyze
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(WORK / "repo" / "shared" / "runtime"))
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "cc100a8ad437"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA = load_selected_generator(TASK, root=ROOT)


def save(name, obj):
    (HERE / name).write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")


def independent_match_windows(grid):
    """An independent scan used as a diagnostic, never as an output authority."""
    panel = [row[:3] for row in grid]
    board = [row[4:] for row in grid]
    occupied = [(r, c, v) for r, row in enumerate(panel)
                for c, v in enumerate(row) if v not in (0, 9)]
    top = min(r for r, c, v in occupied)
    left = min(c for r, c, v in occupied)
    height = max(r for r, c, v in occupied) - top + 1
    width = max(c for r, c, v in occupied) - left + 1
    cells = [(r - top, c - left, v) for r, c, v in occupied]
    hits = [(r, c) for r in range(len(board) - height + 1)
            for c in range(len(board[0]) - width + 1)
            if all(board[r + dr][c + dc] == v for dr, dc, v in cells)]
    return height, width, hits


def prepare():
    catalog = json.loads((HERE / "catalog.json").read_text())
    programs = {row["program_solution"] for row in catalog["variants"]}
    assert len(programs) == 1
    program = programs.pop()
    (HERE / "selected_rule.rkt").write_text(program + "\n", encoding="utf-8")
    save("binding.json", {
        "task_id": TASK,
        "assignment_id": "review-9b33bdf535cc70b3",
        "generator_source": str(SOURCE.relative_to(ROOT)),
        "source_sha256": SOURCE_SHA,
        "version": GEN.VERSION,
        "rule_hash": catalog["rule_hash"],
        "rule_utf8_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "selected_rule_file_sha256": hashlib.sha256((program + "\n").encode()).hexdigest(),
        "prior_evidence_index_sha256": hashlib.sha256(
            (ROOT / "generators" / TASK / "evidence" / "review_index.json").read_bytes()
        ).hexdigest(),
        "source_modified": False,
        "rule_modified": False,
        "notes_modified": False,
        "scope": "findings-only; no approval requested or inferred",
    })
    inputs, cases, failures = [], [], []
    for pair in canonical_pairs(TASK, root=ROOT, labeled_only=True):
        cases.append({
            "input_index": len(inputs), "kind": "canonical",
            "variant": pair["variant"], "split": pair["split"],
            "pair_index": pair["pair_index"], "expected_output": pair["output"],
            "self_check": GEN.self_check(pair["input"]),
        })
        inputs.append(pair["input"])

    recipes = [
        {"seed": seed, "sample_index": index, "difficulty": difficulty, "overrides": {}}
        for difficulty in ("easy", "medium", "hard")
        for seed in (0, 1)
        for index in range(9)
    ]
    exacts = [
        {"grid_h": 6, "board_w": 8, "shape_size": 5, "n_inst": 4, "texture": "varied"},
        {"grid_h": 6, "board_w": 8, "shape_size": 5, "n_inst": 6, "texture": "wide"},
        {"grid_h": 6, "board_w": 8, "shape_size": 5, "n_inst": 6, "texture": "tall"},
        {"grid_h": 16, "board_w": 20, "shape_size": 3, "n_inst": 6, "texture": "varied"},
        {"grid_h": 6, "board_w": 8, "shape_size": 3, "n_inst": 1, "texture": "tall"},
        {"grid_h": 6, "board_w": 8},
    ]
    recipes += [
        {"seed": 0xCC100 + i, "sample_index": i, "difficulty": "hard", "overrides": overrides}
        for i, overrides in enumerate(exacts)
    ]
    for recipe in recipes:
        args = {k: v for k, v in recipe.items() if k != "overrides"}
        try:
            grid = GEN.generate(**args, **recipe["overrides"])
            height, width, hits = independent_match_windows(grid)
            observed = GEN.observe_overrides(grid)
            residues = sorted({(r % height, c % width) for r, c in hits})
            exact_errors = []
            for key, requested in recipe["overrides"].items():
                realized = len(grid) if key == "grid_h" else observed.get(key)
                if key != "texture" and requested != realized:
                    exact_errors.append({"axis": key, "requested": requested, "realized": realized})
            cases.append({
                "input_index": len(inputs), "kind": "generated", "recipe": recipe,
                "self_check": GEN.self_check(grid), "strict_canonical_like": GEN.strict_canonical_like(grid),
                "shape_bbox": [height, width], "independent_match_positions": hits,
                "residues": residues, "observed_axes": observed,
                "override_errors": exact_errors,
                "ordinary_offset_invariant": bool(recipe["overrides"]) or (
                    len(residues) >= 2 and any(r or c for r, c in residues)
                ),
            })
            inputs.append(grid)
        except Exception as exc:
            failures.append({"recipe": recipe, "error_type": type(exc).__name__, "error": str(exc)})

    incompatible_recipe = {
        "seed": 0xCC100, "sample_index": 0, "difficulty": "hard",
        "grid_h": 6, "board_w": 8, "shape_size": 5, "n_inst": 6, "texture": "varied",
    }
    try:
        GEN.generate(**incompatible_recipe)
        expected_rejection = {"recipe": incompatible_recipe, "rejected": False}
    except Exception as exc:
        expected_rejection = {
            "recipe": incompatible_recipe, "rejected": True,
            "error_type": type(exc).__name__, "error": str(exc),
            "interpretation": "Expected: six nonoverlapping 3x3 positive windows cannot fit a 6x8 board.",
        }
    assert len(inputs) <= 64
    save("input.json", inputs)
    save("cases.json", cases)
    save("prepare.json", {
        "source_sha256": SOURCE_SHA, "input_count": len(inputs),
        "generated_recipe_count": len(recipes), "generation_failures": failures,
        "expected_incompatibility": expected_rejection,
    })
    print(json.dumps({"input_count": len(inputs), "generation_failures": failures,
                      "expected_incompatibility_rejected": expected_rejection["rejected"]}))


def analyze():
    payload = json.loads((HERE / "racket.json").read_text())
    binding = json.loads((HERE / "binding.json").read_text())
    cases = json.loads((HERE / "cases.json").read_text())
    inputs = json.loads((HERE / "input.json").read_text())
    prepared = json.loads((HERE / "prepare.json").read_text())
    assert binding["source_sha256"] == SOURCE_SHA == payload["generator_sha256"]
    assert binding["rule_hash"] == payload["executed_rule_hash"] == payload["catalog_rule_hash"]
    # The public apply response hashes the runtime callable separately from
    # the selected source string. Bind its executed normalized rule hash to
    # the selected source; retain both full SHA-256 values without conflating them.
    selected_rule = (HERE / "selected_rule.rkt").read_text().strip()
    normalized_rule_hash = hashlib.sha256(" ".join(selected_rule.split()).encode()).hexdigest()[:12]
    assert binding["rule_hash"] == normalized_rule_hash
    assert binding["rule_utf8_sha256"] == hashlib.sha256(selected_rule.encode()).hexdigest()
    assert len(payload["results"]) == len(cases) == len(inputs)
    findings = list(prepared["generation_failures"])
    rows, groups = [], {}
    rival_counts = {name: {"canonical_disagreements": 0, "ordinary_disagreements": 0,
                           "override_disagreements": 0} for name in GEN.SEMANTIC_RIVALS}
    for case, result in zip(cases, payload["results"]):
        i = case["input_index"]
        assert result["index"] == i and result["input"] == inputs[i]
        grid, out = inputs[i], result["output"]
        errors = []
        if result["error"] or not result["valid_output"]:
            errors.append({"reference_error": result["error"]})
        if result["generator_domain"] != {"status": "valid", "errors": []}:
            errors.append({"generator_domain": result["generator_domain"]})
        if case["self_check"]:
            errors.append({"self_check": case["self_check"]})
        mirror_agrees = GEN.rule_mirror(grid) == out
        if not mirror_agrees:
            errors.append("Python test mirror disagrees with public Racket output")
        canonical_agrees = None
        if case["kind"] == "canonical":
            canonical_agrees = case["expected_output"] == out
            if not canonical_agrees:
                errors.append("Public Racket output disagrees with canonical pair")
        else:
            if case["strict_canonical_like"]:
                errors.append({"strict_canonical_like": case["strict_canonical_like"]})
            if case["override_errors"]:
                errors.append({"override_errors": case["override_errors"]})
            if not case["ordinary_offset_invariant"]:
                errors.append("Ordinary positives do not use independent offset residues")
            recipe = case["recipe"]
            if not recipe["overrides"]:
                groups.setdefault((recipe["difficulty"], recipe["seed"]), []).append((i, grid, out))
        rival_disagreement = {name: fn(grid) != out for name, fn in GEN.SEMANTIC_RIVALS.items()}
        category = ("canonical_disagreements" if case["kind"] == "canonical" else
                    "override_disagreements" if case["recipe"]["overrides"] else
                    "ordinary_disagreements")
        for name, differs in rival_disagreement.items():
            rival_counts[name][category] += differs
        if errors:
            findings.append({"input_index": i, "errors": errors})
        rows.append({"input_index": i, "kind": case["kind"],
                     "input_sha256": result["input_sha256"], "output_sha256": result["output_sha256"],
                     "canonical_output_agrees": canonical_agrees, "mirror_agrees": mirror_agrees,
                     "rival_disagreement": rival_disagreement, "errors": errors})
    lessons = []
    for (difficulty, seed), group in groups.items():
        for start in range(len(group) - 4):
            window = group[start:start + 5]
            demos = [{"input": g, "output": out} for _, g, out in window[:4]]
            query = {"input": window[4][1], "output": window[4][2]}
            failures = GEN.lesson_identifiable(demos, query)
            record = {"difficulty": difficulty, "seed": seed, "start_sample_index": start,
                      "demonstration_input_indices": [i for i, _, _ in window[:4]],
                      "query_input_index": window[4][0], "errors": failures}
            lessons.append(record)
            if failures:
                findings.append({"lesson": record})
    report = {
        "schema": "reviewer-findings-only-audit-v1", "task_id": TASK,
        "source_sha256": SOURCE_SHA, "rule_hash": payload["executed_rule_hash"],
        "rule_text_sha256": payload["rule_text_sha256"],
        "conclusion": "finding" if findings else "no_issue_found_in_bounded_probe",
        "finding_count": len(findings), "findings": findings,
        "canonical_pairs": sum(c["kind"] == "canonical" for c in cases),
        "ordinary_generated_inputs": sum(len(g) for g in groups.values()),
        "exact_or_partial_override_inputs": sum(c["kind"] == "generated" and bool(c["recipe"]["overrides"]) for c in cases),
        "reference_inputs_checked": len(rows), "four_demo_windows_checked": len(lessons),
        "rival_disagreement_counts": rival_counts, "expected_incompatibility": prepared["expected_incompatibility"],
        "case_results": rows, "lesson_results": lessons,
        "limits": [
            "54 ordinary draws cover seeds 0 and 1, sample indices 0 through 8, and all three difficulty bands.",
            "Six targeted override draws are a corner probe, not the full cross-product of axes or seeds.",
            "The three named rivals are incomplete; their refutation does not establish absence of all shortcuts.",
            "No full battery or optional task_tests stage was run; source/rule/notes stayed unchanged.",
            "Catalog approval fields in the raw apply response are preexisting metadata, not this audit's conclusion.",
        ],
    }
    save("report.json", report)
    print(json.dumps({k: report[k] for k in (
        "conclusion", "finding_count", "canonical_pairs", "ordinary_generated_inputs",
        "exact_or_partial_override_inputs", "reference_inputs_checked", "four_demo_windows_checked",
        "rival_disagreement_counts")}, indent=2))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit({"prepare": prepare, "analyze": analyze}[sys.argv[1]]())
