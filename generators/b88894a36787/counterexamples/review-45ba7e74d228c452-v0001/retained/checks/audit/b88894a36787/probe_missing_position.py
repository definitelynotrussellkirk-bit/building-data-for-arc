"""Source-bound, findings-only audit of the omitted four-header reflection.

Run through review.py run. Production labels are obtained separately through
the public arcpuzzles apply command; geometry below is only a diagnostic rival.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "b88894a36787"
OUT = Path(__file__).resolve().parent
ROOT = find_root(Path.cwd())
GEN, SOURCE, SOURCE_SHA = load_selected_generator(TASK, root=ROOT)


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n")


def assumed_missing_position(grid):
    """Rival: use side geometry to guess which header has the missing dot.

    With a missing dot and dots on both edges, always extend header n//2.
    With dots on only one edge, extend the opposite boundary header. Match
    present dots by color and draw their usual L. A missing, unguessed header
    remains at row 0. A guessed header extends to the bottom even if paired.
    """
    h, w = len(grid), len(grid[0])
    header = [(c, color) for c, color in enumerate(grid[0]) if color]
    dots = [(r, c, grid[r][c]) for r in range(1, h) for c in range(w)
            if grid[r][c]]
    guessed = None
    if len(dots) < len(header):
        sides = {c for _, c, _ in dots}
        if len(sides) == 2:
            guessed = len(header) // 2
        elif sides == {0}:
            guessed = len(header) - 1
        elif sides == {w - 1}:
            guessed = 0
    entries = []
    for i, (c, color) in enumerate(header):
        dot = next((item for item in dots if item[2] == color), None)
        target_row, target_col = (dot[0], dot[1]) if dot else (0, None)
        vertical_end = h - 1 if i == guessed else target_row
        entries.append((c, color, target_row, target_col, vertical_end))
    result = [[0] * w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            for hc, color, tr, tc, ve in entries:
                if (c == hc and r <= ve) or (
                    tc is not None and r == tr and min(hc, tc) <= c <= max(hc, tc)
                ):
                    result[r][c] = color
                    break
    return result


def observe(grid):
    h, w = len(grid), len(grid[0])
    header = [(c, color) for c, color in enumerate(grid[0]) if color]
    dots = [(r, c, grid[r][c]) for r in range(1, h) for c in range(w)
            if grid[r][c]]
    present_colors = {value for _, _, value in dots}
    missing = [i for i, (_, color) in enumerate(header) if color not in present_colors]
    return {
        "height": h, "width": w, "header": header, "dots": dots,
        "missing_indices": missing,
        "mixed_sides": {c for _, c, _ in dots} == {0, w - 1},
    }


def prepare():
    canonical = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    declared = {
        "CANONICAL_SHORTCUTS": dict(GEN.CANONICAL_SHORTCUTS),
        "LESSON_COMPETITORS": dict(GEN.LESSON_COMPETITORS),
    }
    summary = {
        "task_id": TASK, "generator_sha256": SOURCE_SHA,
        "generator_source": str(SOURCE.relative_to(ROOT)),
        "rule_hash": GEN.RULE_HASH,
        "canonical_pairs": len(canonical),
        "canonical_rival_fits": sum(assumed_missing_position(p["input"]) == p["output"]
                                    for p in canonical),
        "canonical_self_check_passes": sum(not GEN.self_check(p["input"]) for p in canonical),
        "declared_rivals": {
            declaration: {
                name: {"canonical_matches": sum(fn(p["input"]) == p["output"] for p in canonical),
                       "canonical_pairs": len(canonical)}
                for name, fn in functions.items()
            }
            for declaration, functions in declared.items()
        },
    }
    cases = []
    for i, pair in enumerate(canonical):
        cases.append({
            "id": f"canonical-{i}", "kind": "canonical",
            "canonical_location": {k: v for k, v in pair.items() if k not in ("input", "output")},
            "input": pair["input"], "canonical_output": pair["output"],
            "self_check": GEN.self_check(pair["input"]),
        })
    recipes, unique_hashes, missing_indices = [], set(), Counter()
    invalid, rival_mismatches = [], []
    for band in (None, "easy", "medium", "hard"):
        for seed in (0, 17):
            for h, w in ((11, 15), (15, 11)):
                for n in (2, 3, 4):
                    for index in range(8):
                        overrides = {"grid_h": h, "grid_w": w, "n_markers": n}
                        recipe = {"seed": seed, "sample_index": index,
                                  "difficulty": band, "overrides": overrides}
                        grid = GEN.generate(seed, index, difficulty=band, **overrides)
                        grid_hash = digest(grid)
                        errors = GEN.self_check(grid)
                        obs = observe(grid)
                        unique_hashes.add(grid_hash)
                        if n == 4 and obs["mixed_sides"] and obs["missing_indices"]:
                            missing_indices[str(obs["missing_indices"][0])] += 1
                        if errors:
                            invalid.append({"recipe": recipe, "errors": errors})
                        if assumed_missing_position(grid) != GEN._prediction(grid):
                            rival_mismatches.append(recipe)
                        recipes.append({"recipe": recipe, "input_sha256": grid_hash,
                                        "missing_indices": obs["missing_indices"],
                                        "mixed_sides": obs["mixed_sides"]})
                        selected_shape = (11, 15) if seed == 0 else (15, 11)
                        if band is not None and n == 4 and (h, w) == selected_shape:
                            cases.append({"id": f"generated-{band}-{seed}-{index}",
                                          "kind": "generated", "recipe": recipe,
                                          "input": grid, "self_check": errors})
    overrides = {"grid_h": 11, "grid_w": 11, "n_markers": 4}
    base = GEN.generate(0, 0, **overrides)
    recipe = {"seed": 0, "sample_index": 0, "difficulty": None, "overrides": overrides}
    cases.extend([
        {"id": "base", "kind": "generated", "recipe": recipe,
         "input": base, "self_check": GEN.self_check(base)},
        {"id": "reflected-counterexample", "kind": "counterfactual",
         "recipe": recipe, "transformation": "reverse every input row (horizontal reflection)",
         "input": [row[::-1] for row in base],
         "self_check": GEN.self_check([row[::-1] for row in base]),
         "documented_domain": True,
         "sampler_reachable": False,
         "unreachability": "For 4 headers, phase 0 omits index 2; phase 2 omits boundary index 0 or 3. Phases 1 and 3 have no missing dot. This reflection omits index 1."},
    ])
    summary.update({
        "generated_calls": len(recipes), "unique_generated_inputs": len(unique_hashes),
        "generated_self_check_failures": invalid,
        "generated_rival_vs_python_mirror_mismatches": rival_mismatches,
        "four_header_mixed_side_missing_index_counts": dict(missing_indices),
        "coverage": {"seeds": [0, 17], "sample_indices": list(range(8)),
                     "difficulty": [None, "easy", "medium", "hard"],
                     "shapes": [[11, 15], [15, 11]], "n_markers": [2, 3, 4]},
        "racket_inputs_requested": len(cases), "recipes": recipes,
    })
    save("prepared.json", {"summary": summary, "cases": cases})
    (OUT / "input.json").write_text(json.dumps([c["input"] for c in cases], separators=(",", ":")) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "recipes"}, indent=2))


def verify():
    prepared = json.loads((OUT / "prepared.json").read_text())
    authority = json.loads((OUT / "racket.json").read_text())
    schedule = json.loads((OUT / "schedule-census.json").read_text())
    if prepared["summary"]["generator_sha256"] != SOURCE_SHA:
        raise AssertionError("selected generator changed since prepare")
    assert schedule["generator_sha256"] == SOURCE_SHA == authority["generator_sha256"]
    assert schedule["rule_callable_sha256"] == authority["rule_text_sha256"]
    results = authority["results"]
    assert len(results) == len(prepared["cases"])
    details = []
    for case, result in zip(prepared["cases"], results):
        actual = result["output"]
        grid = case["input"]
        rival = assumed_missing_position(grid)
        assert grid == result["input"]
        assert actual == GEN._prediction(grid)
        if "canonical_output" in case:
            assert actual == case["canonical_output"]
        details.append({"id": case["id"], "kind": case["kind"],
                        "rival_matches_racket": rival == actual,
                        "self_check": GEN.self_check(grid),
                        "input_sha256": digest(grid),
                        "racket_output_sha256": digest(actual)})
        if case["id"] == "reflected-counterexample":
            differences = [[r, c, actual[r][c], rival[r][c]]
                           for r in range(len(grid)) for c in range(len(grid[0]))
                           if actual[r][c] != rival[r][c]]
            evidence = {
                "task_id": TASK, "generator_sha256": SOURCE_SHA,
                "rule_hash": GEN.RULE_HASH,
                "rule_source_sha256": schedule["rule_source_sha256"],
                "authority_receipt": "checks/audit/b88894a36787/racket.json",
                "rule_callable_sha256": authority["rule_text_sha256"],
                "authority_command": authority["command"],
                "authority_cwd": authority["cwd"],
                "recipe": case["recipe"], "transformation": case["transformation"],
                "input": grid, "actual_racket_output": actual, "rival_output": rival,
                "rival_name": "assumed_missing_position", "self_check": GEN.self_check(grid),
                "documented_domain": True, "sampler_reachable": False,
                "unreachability": case["unreachability"], "observed": observe(grid),
                "differing_cells": differences,
                "difference_format": "[row, column, Racket value, rival value]",
                "new_rival_source": "checks/audit/b88894a36787/probe_missing_position.py",
                "new_rival_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            }
            assert differences
            base_index = next(i for i, c in enumerate(prepared["cases"]) if c["id"] == "base")
            assert actual == [row[::-1] for row in results[base_index]["output"]]
            assert not evidence["self_check"]
            evidence["reflection_authority_equivariance"] = True
            save("counterexample.json", evidence)
    assert all(d["rival_matches_racket"] for d in details if d["kind"] != "counterfactual")
    summary = prepared["summary"]
    summary.pop("recipes")
    summary.update({
        "racket_checked_cases": len(details),
        "racket_unique_inputs": len({d["input_sha256"] for d in details}),
        "canonical_rival_racket_matches": sum(d["rival_matches_racket"] for d in details if d["kind"] == "canonical"),
        "generated_rival_racket_matches": sum(d["rival_matches_racket"] for d in details if d["kind"] == "generated"),
        "generated_racket_unique_inputs": len({d["input_sha256"] for d in details if d["kind"] == "generated"}),
        "counterfactual_rival_racket_mismatches": sum(not d["rival_matches_racket"] for d in details if d["kind"] == "counterfactual"),
        "details": details,
    })
    save("probe-results.json", summary)
    print(json.dumps({k: v for k, v in summary.items() if k != "details"}, indent=2))


if __name__ == "__main__":
    {"prepare": prepare, "verify": verify}[sys.argv[1]]()
