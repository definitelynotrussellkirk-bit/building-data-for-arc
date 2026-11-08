"""Findings-only bounded authoring probe for 3642ceca5803; no source edits."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator


TASK_ID = "3642ceca5803"
HERE = Path(__file__).resolve().parent


def digest(value):
    if not isinstance(value, bytes):
        value = json.dumps(value, separators=(",", ":"), sort_keys=True).encode()
    return hashlib.sha256(value).hexdigest()


def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def segments(length, dividers):
    previous = -1
    result = []
    for value in [*dividers, length]:
        if value - previous > 1:
            result.append((previous + 1, value))
        previous = value
    return result


def tiles(grid):
    rows = segments(len(grid), [r for r, row in enumerate(grid) if all(v == 9 for v in row)])
    columns = segments(len(grid[0]), [c for c in range(len(grid[0])) if all(row[c] == 9 for row in grid)])
    return [[row[left:right] for row in grid[top:bottom]]
            for top, bottom in rows for left, right in columns]


def occupancy(grid):
    return [[int(value != 0) for value in row] for row in grid]


def rotate(grid):
    return [list(row) for row in zip(*grid[::-1])]


def tight(grid):
    cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v]
    if not cells:
        return []
    top, bottom = min(r for r, _ in cells), max(r for r, _ in cells)
    left, right = min(c for _, c in cells), max(c for _, c in cells)
    return [row[left:right + 1] for row in grid[top:bottom + 1]]


def third_tile_shortcut(grid):
    return [[8 if v else 0 for v in row] for row in rotate(occupancy(tiles(grid)[2]))]


def structure(grid):
    panels = tiles(grid)
    masks = [occupancy(panel) for panel in panels]
    normalized = [tight(mask) for mask in masks]
    return {
        "input_rows": len(grid), "input_columns": len(grid[0]), "panel_count": len(panels),
        "motif_cell_counts": [sum(map(sum, mask)) for mask in masks],
        "full_tile_rotation_sequence": len(masks) >= 3 and rotate(masks[0]) == masks[1] and rotate(masks[1]) == masks[2],
        "tight_shape_rotation_sequence": len(normalized) >= 3 and bool(normalized[0])
            and rotate(normalized[0]) == normalized[1] and rotate(normalized[1]) == normalized[2],
    }


def prepare():
    root = find_root(__file__)
    module, source, source_hash = load_selected_generator(TASK_ID, root=root)
    rows = [json.loads(line) for line in canonical_path(root).read_text().splitlines()]
    canonical = next(row for row in rows if row.get("task_id") == TASK_ID)
    rule = canonical["program_solution"]
    inputs, cases = [], []

    def add_case(name, grid, *, seed=None, sample_index=None, difficulty=None, overrides=None, domain="generated"):
        key = digest(grid)
        input_index = next((i for i, item in enumerate(inputs) if digest(item) == key), None)
        if input_index is None:
            input_index = len(inputs)
            inputs.append(grid)
        cases.append({"name": name, "input_index": input_index, "input_sha256": key,
                      "seed": seed, "sample_index": sample_index, "difficulty": difficulty,
                      "overrides": overrides or {}, "self_check": module.self_check(grid, difficulty=difficulty),
                      "support_scope": domain, "structure": structure(grid)})

    base = module.generate(0, 0)
    add_case("generated_base", base, seed=0, sample_index=0)
    changed = [row[:] for row in base]
    columns = segments(len(base[0]), [c for c in range(len(base[0])) if all(row[c] == 9 for row in base)])
    for panel_index, color in ((0, 2), (1, 3)):
        left, right = columns[panel_index]
        for row in changed:
            row[left:right] = [0] * (right - left)
        changed[0][left] = color
        changed[1][left] = color
        changed[1][left + 1] = color
    add_case("context_counterfactual", changed, domain="hand-constructed within documented panel/motif domain; generator support not claimed")
    for size in (1, 4):
        grid = module.generate(0, 0, motif_size=size)
        add_case(f"motif_size_{size}", grid, seed=0, sample_index=0, overrides={"motif_size": size})

    census = []
    blank_witness_added = False
    for difficulty, stop in ((None, 64), ("easy", 256)):
        for seed in range(stop):
            sample_index = seed % 7
            grid = module.generate(seed, sample_index, difficulty=difficulty)
            info = structure(grid)
            status = module.self_check(grid, difficulty=difficulty)
            row = {"seed": seed, "sample_index": sample_index, "difficulty": difficulty,
                   "input_sha256": digest(grid), "self_check": status, **info}
            census.append(row)
            if difficulty == "easy" and info["motif_cell_counts"][2] == 0 and not blank_witness_added:
                add_case("empty_third_panel", grid, seed=seed, sample_index=sample_index, difficulty=difficulty)
                blank_witness_added = True
    canonical_checks = []
    for pair in canonical_pairs(TASK_ID, root=root):
        predicted = third_tile_shortcut(pair["input"])
        canonical_checks.append({"variant": pair["variant"], "split": pair["split"], "pair_index": pair["pair_index"],
                                 "input_sha256": digest(pair["input"]), "output_sha256": digest(pair["output"]),
                                 "shortcut_matches_canonical_label": predicted == pair["output"]})
        add_case(f"canonical_{pair['variant']}_{pair['split']}_{pair['pair_index']}", pair["input"], domain="canonical_only")
    write("input.json", inputs)
    write("rival-output.json", [{"input_index": i, "input_sha256": digest(grid), "output": third_tile_shortcut(grid)}
                               for i, grid in enumerate(inputs)])
    write("census.json", census)
    report = {
        "task_id": TASK_ID, "generator_sha256": source_hash,
        "generator_path": source.relative_to(root).as_posix(),
        "canonical_program_sha256": hashlib.sha256(rule.encode()).hexdigest(),
        "canonical_normalized_program_sha256": hashlib.sha256(" ".join(rule.split()).encode()).hexdigest(),
        "canonical_title": canonical["title"], "canonical_written_solution": canonical["written_solution"],
        "generator_version": module.VERSION, "cases": cases, "canonical_rival_checks": canonical_checks,
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "third_panel_equal_in_counterfactual": tiles(base)[2] == tiles(changed)[2],
        "census_scope": {"default": {"seed_range_inclusive": [0, 63], "sample_index": "seed % 7"},
                         "easy": {"seed_range_inclusive": [0, 255], "sample_index": "seed % 7"}},
        "prior_finding": {"status": "needs_triage", "return_id": "review-38a3c9f6f591dcde:v0001",
                          "same_source": source_hash == "79a1302891ee8d1bd5edfeb55e47a2ea32b1a05983fa05a3b66650ab4ecf6233"},
        "reference_outputs_pending": True,
    }
    write("preparation.json", report)
    print(json.dumps({"unique_reference_inputs": len(inputs), "case_count": len(cases),
                      "census_inputs": len(census), "empty_third_witness_found": blank_witness_added,
                      "generator_sha256": source_hash, "canonical_program_sha256": report["canonical_program_sha256"]}, indent=2))


def analyze():
    prepared = json.loads((HERE / "preparation.json").read_text())
    actual = json.loads((HERE / "racket.json").read_text())
    rivals = json.loads((HERE / "rival-output.json").read_text())
    census = json.loads((HERE / "census.json").read_text())
    assert actual["generator_sha256"] == prepared["generator_sha256"]
    # The public receipt's rule_text_sha256 binds its executable lambda, while
    # executed_rule_hash is the 12-character normalized canonical-source hash.
    assert actual["executed_rule_hash"] == prepared["canonical_normalized_program_sha256"][:12]
    inputs = json.loads((HERE / "input.json").read_text())
    assert all(row["input"] == inputs[row["index"]] for row in actual["results"])
    reference_checks = [{"input_index": row["index"], "error": row["error"],
                         "valid_output": row["valid_output"], "output": row["output"],
                         "shortcut_match": row["output"] == rivals[row["index"]]["output"]}
                        for row in actual["results"]]
    by_case = {case["name"]: case for case in prepared["cases"]}
    by_input = {row["input_index"]: row for row in reference_checks}
    counts = {}
    for difficulty in (None, "easy"):
        selected = [row for row in census if row["difficulty"] == difficulty]
        counts[str(difficulty)] = {
            "samples": len(selected), "self_check_accepted": sum(not row["self_check"] for row in selected),
            "full_tile_rotation_sequences": sum(row["full_tile_rotation_sequence"] for row in selected),
            "tight_shape_rotation_sequences": sum(row["tight_shape_rotation_sequence"] for row in selected),
            "empty_third_panels": sum(row["motif_cell_counts"][2] == 0 for row in selected),
            "any_empty_panel": sum(0 in row["motif_cell_counts"] for row in selected),
        }
    context_equal = (by_input[by_case["generated_base"]["input_index"]]["output"]
                     == by_input[by_case["context_counterfactual"]["input_index"]]["output"])
    motif_control = {
        "size_1_and_4_inputs_identical": by_case["motif_size_1"]["input_sha256"] == by_case["motif_size_4"]["input_sha256"],
        "size_1_motif_cell_counts": by_case["motif_size_1"]["structure"]["motif_cell_counts"],
        "size_1_has_larger_motifs": max(by_case["motif_size_1"]["structure"]["motif_cell_counts"]) > 1,
        "validator_accepts_size_1": not by_case["motif_size_1"]["self_check"],
    }
    blank = by_case.get("empty_third_panel")
    if blank:
        output = by_input[blank["input_index"]]["output"]
        blank = {**blank, "racket_output": output, "output_all_zero": not any(v for row in output for v in row)}
    report = {**prepared, "reference_outputs_pending": False, "reference_checks": reference_checks,
              "executed_rule_hash": actual["executed_rule_hash"],
              "rule_text_sha256": actual["rule_text_sha256"], "counts": counts,
              "context_counterfactual_outputs_equal": context_equal, "motif_control": motif_control,
              "empty_third_witness": blank,
              "reference_count": len(reference_checks),
              "reference_passed": sum(row["valid_output"] and not row["error"] for row in reference_checks),
              "shortcut_matches_reference": sum(row["shortcut_match"] for row in reference_checks),
              "canonical_rival_pairs": len(prepared["canonical_rival_checks"]),
              "canonical_rival_passed": sum(row["shortcut_matches_canonical_label"] for row in prepared["canonical_rival_checks"]),
              "limitations": "The structural census is finite and only selected retained inputs were Racket-executed; no production lesson identifiability, all seeds, or additional rivals were certified."}
    write("audit-report.json", report)
    print(json.dumps({key:report[key] for key in ["counts","context_counterfactual_outputs_equal","motif_control",
                                                "reference_count","reference_passed","shortcut_matches_reference",
                                                "canonical_rival_pairs","canonical_rival_passed"]}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "analyze"))
    args = parser.parse_args()
    prepare() if args.action == "prepare" else analyze()
