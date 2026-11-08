"""Findings-only, direct-source audit. Does not alter any generator or stage a runtime."""
from collections import deque
from hashlib import sha256
from pathlib import Path
import json
import sys

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))
from reviewer_support import canonical_pairs, load_selected_generator

TASK = "6c16d20079af"


def save(name, value):
    path = HERE / name
    path.write_text(json.dumps(value, separators=(",", ":")) + "\n")
    return {"path": str(path.relative_to(WORK)), "sha256": sha256(path.read_bytes()).hexdigest()}


def describe(grid):
    """Independent any-color 4-connected component and enclosed-zero inspection."""
    height, width = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(height) for c in range(width)
                 if grid[r][c] not in (0, 8, 9)}
    components = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue = deque([start])
        cells = []
        while queue:
            r, c = queue.popleft()
            cells.append((r, c))
            for neighbor in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    queue.append(neighbor)
        r0, r1 = min(r for r, c in cells), max(r for r, c in cells)
        c0, c1 = min(c for r, c in cells), max(c for r, c in cells)
        zeros = {(r, c) for r in range(r0, r1+1) for c in range(c0, c1+1)
                 if grid[r][c] == 0}
        boundary = {(r, c) for r, c in zeros if r in (r0, r1) or c in (c0, c1)}
        outside = set(boundary)
        queue = deque(boundary)
        while queue:
            r, c = queue.popleft()
            for neighbor in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                if neighbor in zeros and neighbor not in outside:
                    outside.add(neighbor)
                    queue.append(neighbor)
        components.append({
            "bbox_r0_c0_r1_c1": [r0, c0, r1, c1],
            "colors": sorted({grid[r][c] for r, c in cells}),
            "cell_count": len(cells),
            "bbox_interior_zero_count": sum(r0 < r < r1 and c0 < c < c1 for r, c in zeros),
            "enclosed_zero_count": len(zeros - outside),
        })
    return {"height": height, "width": width, "components": components,
            "holed_component_indices": [i for i, c in enumerate(components) if c["enclosed_zero_count"]]}


def main():
    module, source_path, source_sha = load_selected_generator(TASK, root=REPO)
    ledger_path = REPO / "shared/data/canonical/puzzles.jsonl"
    matches = [(raw, json.loads(raw)) for raw in ledger_path.read_bytes().splitlines(keepends=True)
               if json.loads(raw).get("task_id") == TASK]
    assert len(matches) == 1
    raw, canonical = matches[0]
    rule = canonical["program_solution"]
    result = {
        "schema": "focused-generator-audit-v1", "task_id": TASK,
        "source": {"path": str(source_path.relative_to(REPO)), "sha256": source_sha},
        "canonical": {"path": str(ledger_path.relative_to(REPO)), "matching_rows": len(matches),
                      "exact_row_including_newline_sha256": sha256(raw).hexdigest(),
                      "program_solution_utf8_sha256": sha256(rule.encode()).hexdigest()},
        "helper_path": "shared/runtime/reviewer_support.py",
        "canonical_checks": [],
    }
    for pair in canonical_pairs(TASK, root=REPO, labeled_only=True):
        record = {k: pair[k] for k in ("variant", "split", "pair_index")}
        record["self_check"] = module.self_check(pair["input"])
        record["description"] = describe(pair["input"])
        if pair["split"] == "train" and pair["pair_index"] == 2:
            record["input_asset"] = save("canonical_train2_input.json", pair["input"])
            record["canonical_output_asset"] = save("canonical_train2_expected.json", pair["output"])
        result["canonical_checks"].append(record)

    override_recipe = {"seed": 123, "sample_index": 5, "difficulty": "easy", "overrides": {"n_solid": 3}}
    override_grid = module.generate(123, 5, difficulty="easy", n_solid=3)
    override_description = describe(override_grid)
    result["ignored_exact_override"] = {
        "recipe": override_recipe, "input_asset": save("override_input.json", override_grid),
        "self_check": module.self_check(override_grid), "description": override_description,
        "actual_solid_count": sum(c["enclosed_zero_count"] == 0 for c in override_description["components"]),
        "identical_to_call_without_override": override_grid == module.generate(123, 5, difficulty="easy"),
        "domain_status": "Exact unmodified output of public generate; n_solid=3 is declared valid but ignored.",
    }

    recipe = {"seed": 0, "sample_index": 0, "difficulty": "easy",
              "overrides": {"grid_h": 11, "grid_w": 11}}
    generated = module.generate(0, 0, difficulty="easy", grid_h=11, grid_w=11)
    description = describe(generated)
    r0, c0, r1, c1 = description["components"][0]["bbox_r0_c0_r1_c1"]
    mutated = [row[:] for row in generated]
    old = mutated[r0][c0+1]
    mutated[r0][c0+1] = 0
    result["one_cell_opening"] = {
        "base_recipe": recipe,
        "generated_input_asset": save("input.json", generated),
        "generated_self_check": module.self_check(generated),
        "generated_description": description,
        "mutation": {"row": r0, "column": c0+1, "from": old, "to": 0},
        "mutated_input_asset": save("open_ring_input.json", mutated),
        "mutated_self_check": module.self_check(mutated),
        "mutated_description": describe(mutated),
        "domain_status": "Base is emitted with supported exact dimensions; mutant is a one-cell adversarial change, not an emitted sample. It retains valid palette, dimensions, padding, isolated key and solid distractor, but violates the canonical requirement for an enclosed hole.",
    }

    # Small direct-source coverage check, not a battery or Racket verification.
    result["sample_probe"] = {"seed_range_inclusive": [0, 127], "sample_index": 0,
                             "difficulties": ["easy", "medium", "hard"],
                             "overrides": {}, "count": 0, "self_check_failures": [],
                             "non_topmost_enclosed_targets": [], "no_enclosed_target": []}
    sample = result["sample_probe"]
    for difficulty in sample["difficulties"]:
        for seed in range(128):
            grid = module.generate(seed, 0, difficulty=difficulty)
            errors = module.self_check(grid)
            info = describe(grid)
            sample["count"] += 1
            if errors:
                sample["self_check_failures"].append({"seed": seed, "difficulty": difficulty, "errors": errors})
            if not info["holed_component_indices"]:
                sample["no_enclosed_target"].append({"seed": seed, "difficulty": difficulty})
            elif info["holed_component_indices"][0] != 0:
                sample["non_topmost_enclosed_targets"].append({"seed": seed, "difficulty": difficulty})
    assert module.self_check(mutated) == []
    assert not describe(mutated)["holed_component_indices"]
    assert result["ignored_exact_override"]["actual_solid_count"] == 2
    reference_names = ["racket.json", "open_ring_racket.json"]
    if all((HERE / name).is_file() for name in reference_names):
        references = []
        for name, expected_input in zip(reference_names, [generated, mutated]):
            path = HERE / name
            reference = json.loads(path.read_text())
            observed = reference["results"][0]
            assert reference["task_id"] == TASK
            assert reference["generator_sha256"] == source_sha
            assert reference["rule_hash_matches_catalog"] is True
            assert reference["executed_rule_hash"] == sha256(rule.encode()).hexdigest()[:12]
            assert observed["input"] == expected_input
            references.append({
                "asset": {"path": str(path.relative_to(WORK)), "sha256": sha256(path.read_bytes()).hexdigest()},
                "generator_sha256": reference["generator_sha256"],
                "executed_rule_hash": reference["executed_rule_hash"],
                "catalog_rule_hash": reference["catalog_rule_hash"],
                "rule_hash_matches_catalog": reference["rule_hash_matches_catalog"],
                "executed_rule_text_sha256": reference["rule_text_sha256"],
                "input_matches_retained_grid": True,
                "output": observed["output"],
                "valid_output": observed["valid_output"],
                "error": observed["error"],
            })
        assert references[0]["valid_output"] is True
        assert references[0]["output"] == [[3,3,3,3],[3,8,8,3],[3,8,8,3],[3,3,3,3]]
        assert references[1]["valid_output"] is False
        assert references[1]["output"] is None and references[1]["error"]
        result["fresh_reference_execution"] = {
            "basis": "Two parent-executed serial public apply commands; this probe verifies their saved inputs, source/rule bindings and outcomes without launching another runtime.",
            "commands_asset": "checks/audit/6c16d20079af/racket-commands.json",
            "base": references[0], "one_cell_mutant": references[1],
        }
    save("probe.json", result)
    print(json.dumps({"task_id": TASK, "source_sha256": source_sha,
                      "rule_sha256": result["canonical"]["program_solution_utf8_sha256"],
                      "canonical_rejected_pairs": [p["pair_index"] for p in result["canonical_checks"] if p["self_check"]],
                      "override_actual_solids": result["ignored_exact_override"]["actual_solid_count"],
                      "mutation": result["one_cell_opening"]["mutation"],
                      "mutant_self_check": result["one_cell_opening"]["mutated_self_check"],
                      "mutant_enclosed_targets": describe(mutated)["holed_component_indices"],
                      "sample_probe": sample}, indent=2))


if __name__ == "__main__":
    main()
