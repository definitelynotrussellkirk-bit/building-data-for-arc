#!/usr/bin/env python3
"""Findings-only audit; source and authority files are never changed."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT / "repo"
HERE = Path(__file__).resolve().parent
TASK = "d2f386d0e071"
sys.path.insert(0, str(REPO / "shared/runtime"))
SPEC = importlib.util.spec_from_file_location("audited_mirror", REPO / "generators" / TASK / "generator.py")
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    found = []
    for row in range(height):
        for col in range(width):
            if not grid[row][col] or (row, col) in seen:
                continue
            color = grid[row][col]
            todo = [(row, col)]
            seen.add((row, col))
            group = []
            while todo:
                r, c = todo.pop()
                group.append((r, c))
                for rr, cc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                    if 0 <= rr < height and 0 <= cc < width and (rr,cc) not in seen and grid[rr][cc] == color:
                        seen.add((rr,cc))
                        todo.append((rr,cc))
            found.append((color, sorted(group)))
    return found


def rigid_component_copy(grid):
    """Keep sources; translate each monochromatic 4-component into reflected bbox."""
    output = [row[:] for row in grid]
    width = len(grid[0])
    for color, group in components(grid):
        lo = min(c for _, c in group)
        hi = max(c for _, c in group)
        offset = width - 1 - hi - lo
        for row, col in group:
            output[row][col + offset] = color
    return output


def leftmost_per_row(grid):
    output = [row[:] for row in grid]
    width = len(grid[0])
    for r, row in enumerate(grid):
        occupied = [c for c, color in enumerate(row) if color]
        if occupied:
            c = occupied[0]
            output[r][width - 1 - c] = row[c]
    return output


def singleton_components_only(grid):
    output = [row[:] for row in grid]
    width = len(grid[0])
    for color, group in components(grid):
        if len(group) == 1:
            row, col = group[0]
            output[row][width - 1 - col] = color
    return output


def one_mark_per_color(grid):
    output = [row[:] for row in grid]
    seen = set()
    width = len(grid[0])
    for row, values in enumerate(grid):
        for col, color in enumerate(values):
            if color and color not in seen:
                seen.add(color)
                output[row][width - 1 - col] = color
    return output


RIVALS = {
    "rigid_component_copy": rigid_component_copy,
    "leftmost_per_row": leftmost_per_row,
    "singleton_components_only": singleton_components_only,
    "one_mark_per_color": one_mark_per_color,
}


def main():
    census_path = HERE / "lesson-census.json"
    census = json.loads(census_path.read_text())
    canonical = next(json.loads(line) for line in (REPO / "shared/data/canonical/puzzles.jsonl").read_text().splitlines() if json.loads(line).get("task_id") == TASK)
    canonical_pairs = canonical["train"] + canonical["test"]
    generator_hash = file_hash(Path(GEN.__file__))
    assert generator_hash == census["generator_sha256"]
    assert census["status"] == "no_ambiguity_found"
    source = {key: census[key] for key in ("generator_sha256", "rule_source_sha256", "rule_callable_sha256", "declared_rule_hash")}
    source.update({"canonical_file_sha256": file_hash(REPO / "shared/data/canonical/puzzles.jsonl"), "canonical_row_sha256": digest(canonical), "probe_sha256": file_hash(Path(__file__)), "census_sha256": file_hash(census_path)})
    declared = {}
    for attr in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS", "SEMANTIC_RIVALS"):
        for name, fn in getattr(GEN, attr, {}).items():
            declared[attr + ":" + name] = fn
    canonical_fit = {name: {"fits": sum(fn(p["input"]) == p["output"] for p in canonical_pairs), "pairs": len(canonical_pairs)} for name, fn in {**declared, **RIVALS}.items()}
    defaults = []
    lessons = []
    ambiguous = []
    for lesson in census["lessons"]:
        inst = lesson["instance"]
        sampling = inst["sampling"]
        pairs = inst["train"] + inst["test"]
        accepted = sampling["accepted_pairs"]
        assert len(accepted) == len(pairs) == 5
        scores = {}
        for name, fn in RIVALS.items():
            fits = all(fn(p["input"]) == p["output"] for p in inst["train"])
            query_agrees = all(fn(p["input"]) == p["output"] for p in inst["test"])
            scores[name] = "refuted" if not fits else "survived_all" if query_agrees else "ambiguous"
        lesson_row = {"band": lesson["band"], "index": lesson["index"], "seed": lesson["seed"], "requested_start": sampling["requested_start"], "accepted_indices": [a["sample_index"] for a in accepted], "rejections": sampling["rejections"], "scores": scores}
        lessons.append(lesson_row)
        if "ambiguous" in scores.values():
            ambiguous.append({**lesson_row, "instance": inst})
        for pair, accepted_pair in zip(pairs, accepted):
            assert digest(pair["input"]) == accepted_pair["input_sha256"]
            assert GEN.generate(lesson["seed"], accepted_pair["sample_index"], difficulty=lesson["band"]) == pair["input"]
            defaults.append({"band": lesson["band"], "lesson_index": lesson["index"], "seed": lesson["seed"], "sample_index": accepted_pair["sample_index"], "overrides": {}, "input_sha256": digest(pair["input"]), "validator_errors": GEN.self_check(pair["input"]), "strict_errors": GEN.strict_canonical_like(pair["input"]), "python_mirror_matches_executed_racket": GEN.rule_mirror(pair["input"]) == pair["output"], "rival_agreement": {name: fn(pair["input"]) == pair["output"] for name, fn in RIVALS.items()}})
    controls = []
    witnesses = []
    for index in range(75):
        band = ("easy", "medium", "hard")[index % 3]
        seed = 50000 + index
        overrides = {"grid_h": 5, "grid_w": 7, "n_cells": 9, "n_distinct_colors": 2}
        grid = GEN.generate(seed, index, difficulty=band, **overrides)
        python_output = GEN.rule_mirror(grid)
        rival_output = rigid_component_copy(grid)
        rec = {"seed": seed, "sample_index": index, "difficulty": band, "overrides": overrides, "input_sha256": digest(grid), "validator_errors": GEN.self_check(grid), "strict_errors": GEN.strict_canonical_like(grid), "observed_overrides": GEN.observe_overrides(grid), "rigid_copy_matches_python_oracle": rival_output == python_output}
        controls.append(rec)
        if rival_output != python_output:
            witnesses.append({**source, **rec, "input": grid, "rival_name": "rigid_component_copy", "rival_output": rival_output, "python_oracle_output": python_output, "actual_racket_output": None, "domain_status": "Directly generated using declared exact controls; validator and strict predicate are recorded. Not an ordinary default draw.", "components": components(grid)})
    assert witnesses, "Targeted lawful controls did not expose rigid-copy rival"
    assert all(not x["validator_errors"] and not x["strict_errors"] for x in defaults + controls)
    selected = witnesses[0]
    all_inputs = [p["input"] for p in canonical_pairs]
    input_labels = [{"kind": "canonical", "pair_index": index, "labels_are_copied_until_apply": True} for index in range(len(canonical_pairs))]
    for lesson in ambiguous:
        start = len(all_inputs)
        all_inputs.extend(p["input"] for p in lesson["instance"]["train"] + lesson["instance"]["test"])
        input_labels.extend({"kind": "production_ambiguity", "band": lesson["band"], "lesson_index": lesson["index"], "pair_index": i} for i in range(5))
        lesson["apply_result_indices"] = list(range(start, start + 5))
    selected["apply_result_index"] = len(all_inputs)
    all_inputs.append(selected["input"])
    input_labels.append({"kind": "rigid_copy_control", "seed": selected["seed"], "sample_index": selected["sample_index"]})
    assert len(all_inputs) <= 64
    write("input.json", all_inputs)
    write("input-map.json", input_labels)
    write("rigid-copy-witness.json", selected)
    write("production-ambiguities.json", ambiguous)
    summary = {"task_id": TASK, "source": source, "default_pairs": len(defaults), "default_unique_inputs": len({x["input_sha256"] for x in defaults}), "default_validator_passes": sum(not x["validator_errors"] for x in defaults), "default_python_mirror_racket_matches": sum(x["python_mirror_matches_executed_racket"] for x in defaults), "targeted_controls": len(controls), "control_unique_inputs": len({x["input_sha256"] for x in controls}), "control_validator_passes": sum(not x["validator_errors"] for x in controls), "control_rigid_copy_differences_against_python_oracle": len(witnesses), "control_labels_status": "Python-oracle screening only; selected witness will be independently executed with supported apply command.", "canonical_rival_fit": canonical_fit, "declared_namespaces": {attr: list(getattr(GEN, attr, {})) for attr in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS", "SEMANTIC_RIVALS")}, "lesson_scores": lessons, "default_draws": defaults, "control_draws": controls, "production_ambiguous_lessons": len(ambiguous), "production_ambiguities_by_rival": {name: sum(row["scores"][name] == "ambiguous" for row in lessons) for name in RIVALS}, "default_agreement_by_rival": {name: sum(row["rival_agreement"][name] for row in defaults) for name in RIVALS}, "sampler": census["sampler"], "accepted_pair_residues": {band: {key: report[key] for key in ("accepted_indices_recorded", "accepted_pair_residues", "start_residues")} for band, report in census["per_band"].items()}, "production_rejections": sum(len(row["rejections"]) for row in lessons), "apply_input_count": len(all_inputs), "limits": ["45 production lessons (15 per band), 225 distinct pairs; no query rotations.", "75 direct targeted controls with Python-oracle screening; authoritative application is a separate command.", "No generator/rule/source changes and no full battery.", "Declared census no_ambiguity_found covers only declared rivals; new rivals are scored separately.", "Rigid component copy agrees on every default input by a color-multiplicity argument; a controlled counterexample is not a failed default production query."]}
    write("probe-summary.json", summary)
    print(json.dumps({key: summary[key] for key in ("default_pairs", "default_unique_inputs", "default_validator_passes", "default_python_mirror_racket_matches", "targeted_controls", "control_unique_inputs", "control_validator_passes", "control_rigid_copy_differences_against_python_oracle", "production_ambiguous_lessons", "production_ambiguities_by_rival", "default_agreement_by_rival", "apply_input_count")}, indent=2))


if __name__ == "__main__":
    main()
