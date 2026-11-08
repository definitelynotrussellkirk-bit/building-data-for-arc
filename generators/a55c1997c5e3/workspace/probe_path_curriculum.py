#!/usr/bin/env python3
"""Small public-API path-curriculum probe with separately retained Racket labels.

This is a representative-shape diagnostic, not a production lesson census.
It discovers the live declarations and never uses a Python mirror for labels.
See the workspace README for prepare/apply/score commands and evidence scope.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys


TASK = "a55c1997c5e3"


def bootstrap():
    """Locate only dependencies in this repository or a copied runtime."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        for relative in ("shared/runtime", "."):
            runtime = parent / relative
            if (runtime / "reviewer_support.py").is_file():
                sys.path.insert(0, str(runtime))
                from reviewer_support import find_root
                return find_root(here)
    raise RuntimeError("No local public reviewer_support helper")


def grid_hash(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    if path.exists():
        raise FileExistsError(f"Refusing to replace retained evidence: {path}")
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def selected(root):
    from reviewer_support import load_selected_generator
    return load_selected_generator(TASK, root=root)


def rival_inventory(gen):
    """Deduplicate same-name aliases to the exact callable object in this run."""
    inventory, functions, identities = [], {}, {}
    for namespace in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS"):
        declaration = getattr(gen, namespace, {})
        if not isinstance(declaration, dict):
            raise TypeError(f"{namespace} must be a dict")
        for name, function in declaration.items():
            if not isinstance(name, str) or not callable(function):
                raise TypeError(f"Invalid declaration {namespace}:{name!r}")
            identity = (name, id(function))
            if identity not in identities:
                rival_id = f"r{len(inventory)}"
                identities[identity] = rival_id
                inventory.append({"id": rival_id, "name": name, "bindings": []})
                functions[rival_id] = function
            rival_id = identities[identity]
            row = next(row for row in inventory if row["id"] == rival_id)
            row["bindings"].append(f"{namespace}:{name}")
    if not inventory:
        raise ValueError("No declared rivals to inspect")
    return inventory, functions


def predict(function, grid):
    from reviewer_support import normalize_grid
    predictions = []
    for _ in range(2):
        copied = deepcopy(grid)
        prediction = normalize_grid(function(copied))
        if copied != grid:
            raise ValueError("Rival mutated its input")
        predictions.append(prediction)
    if predictions[0] != predictions[1]:
        raise ValueError("Rival prediction is not deterministic")
    return predictions[0]


def minimal_left_up():
    grid = [[0] * 18 for _ in range(16)]
    for r, c, color in ((0, 3, 8), (3, 0, 8), (3, 3, 2)):
        for rr in (r, r + 1):
            for cc in (c, c + 1):
                grid[rr][cc] = color
    return grid


def prepare(args, root):
    from reviewer_support import canonical_pairs, normalize_grid
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    gen, source, source_sha = selected(root)
    inventory, functions = rival_inventory(gen)
    canonical = canonical_pairs(TASK, root=root, labeled_only=True)
    profiles = tuple(getattr(gen, "SCENE_PROFILES", ()))
    period = getattr(gen, "LESSON_SCHEDULE_PERIOD", None)
    examples = getattr(gen, "EXAMPLES_NEEDED", None)
    if type(period) is not int or not 1 <= period <= 64:
        raise ValueError("This bounded probe requires a declared period in 1..64")
    if type(examples) is not int or not 1 <= examples <= 16:
        raise ValueError("This bounded probe requires EXAMPLES_NEEDED in 1..16")
    records, inputs, predictions, alternative_outputs = [], [], [], {}

    def keep(label, grid, *, kind, recipe=None, canonical_output=None):
        grid = normalize_grid(grid)
        index = len(inputs)
        row = {
            "index": index, "label": label, "kind": kind,
            "input_sha256_probe": grid_hash(grid), "generate_call": recipe,
            "self_check": gen.self_check(deepcopy(grid)),
            "strict_canonical_like": gen.strict_canonical_like(deepcopy(grid)),
            "observables": gen.semantic_observables(deepcopy(grid)),
            "witnesses": {name: bool(fn(deepcopy(grid)))
                          for name, fn in getattr(gen, "SEMANTIC_WITNESSES", {}).items()},
        }
        if canonical_output is not None:
            row["canonical_output_sha256_probe"] = grid_hash(canonical_output)
        predicted = {}
        for rival_id, function in functions.items():
            output = predict(function, grid)
            output_hash = grid_hash(output)
            predicted[rival_id] = {"sha256_probe": output_hash}
            # Share exact repeated grids without conflating rival identities.
            # Alternatives remain separate from the authoritative labels.
            alternative_outputs[output_hash] = output
        records.append(row)
        inputs.append(grid)
        predictions.append(predicted)
        return index

    for index, pair in enumerate(canonical):
        keep(f"canonical_{index}", pair["input"], kind="canonical",
             canonical_output=pair["output"])
    representatives = {}
    for index, profile in enumerate(profiles):
        recipe = {"seed": args.seed, "sample_index": index,
                  "difficulty": args.difficulty,
                  "overrides": {"scene_profile": profile,
                                "grid_h": args.grid_h, "grid_w": args.grid_w}}
        grid = gen.generate(args.seed, index, difficulty=args.difficulty,
                            **recipe["overrides"])
        if gen.observe_overrides(grid).get("scene_profile") != profile:
            raise ValueError(f"Profile did not round trip: {profile}")
        representatives[profile] = keep(profile, grid, kind="generated_representative", recipe=recipe)
    keep("minimal_left_up_tie", minimal_left_up(), kind="handmade_lawful_counterexample")
    if len(inputs) > 64:
        raise ValueError("Public apply batch limit is 64 inputs")

    windows = []
    for start in range(period):
        schedule = [gen.schedule_profile(args.seed, start + offset, args.difficulty)
                    for offset in range(examples + 1)]
        windows.append({"start": start, "profiles": schedule,
                        "representative_indices": [representatives[name] for name in schedule]})
    write_json(out / "inputs.json", {"inputs": inputs})
    write_json(out / "alternatives.json", alternative_outputs)
    write_json(out / "prepared.json", {
        "schema": "a55c1997c5e3-path-representatives-v1",
        "scope": "Rival predictions only; public Racket labels required before scoring",
        "task_id": TASK, "generator_source": str(source), "generator_sha256": source_sha,
        "probe_sha256": file_hash(Path(__file__)), "inputs_sha256": file_hash(out / "inputs.json"),
        "alternatives_sha256": file_hash(out / "alternatives.json"),
        "seed": args.seed, "difficulty": args.difficulty,
        "period": period, "examples_needed": examples,
        "inventory": inventory, "records": records, "predictions": predictions,
        "representatives": representatives, "windows": windows,
    })
    print(json.dumps({"status": "prepared", "output": str(out),
                      "generator_sha256": source_sha, "inputs": len(inputs),
                      "unique_rivals": len(inventory),
                      "declaration_bindings": sum(len(row["bindings"]) for row in inventory)}))


def apply(args, root):
    out = args.out.resolve()
    prepared = json.loads((out / "prepared.json").read_text())
    _, _, current_sha = selected(root)
    if current_sha != prepared["generator_sha256"]:
        raise ValueError("Selected generator changed after prepare; use a new evidence directory")
    if file_hash(out / "inputs.json") != prepared["inputs_sha256"]:
        raise ValueError("Prepared input bytes changed")
    if file_hash(out / "alternatives.json") != prepared["alternatives_sha256"]:
        raise ValueError("Prepared alternative prediction bytes changed")
    command = [sys.executable, "-m", "arcpuzzles", "apply", TASK,
               "--input", str(out / "inputs.json"), "--out", str(out / "racket.json")]
    subprocess.run(command, cwd=root, check=True)


def score(args, root):
    out = args.out.resolve()
    prepared = json.loads((out / "prepared.json").read_text())
    receipt = json.loads((out / "racket.json").read_text())
    inputs = json.loads((out / "inputs.json").read_text())["inputs"]
    gen, _, current_sha = selected(root)
    if receipt["generator_sha256"] != prepared["generator_sha256"] or current_sha != prepared["generator_sha256"]:
        raise ValueError("Generator source differs between prepare, public apply, and score")
    if receipt["task_id"] != TASK or receipt["reference"] != "canonical":
        raise ValueError("Expected this task's canonical public apply receipt")
    if file_hash(out / "inputs.json") != prepared["inputs_sha256"]:
        raise ValueError("Prepared input bytes changed")
    if file_hash(out / "alternatives.json") != prepared["alternatives_sha256"]:
        raise ValueError("Prepared alternative prediction bytes changed")
    if len(receipt["results"]) != len(inputs):
        raise ValueError("Incomplete Racket result population")
    authoritative, output_hashes = [], []
    for index, row in enumerate(receipt["results"]):
        if row["input"] != inputs[index] or row.get("error") is not None or not row.get("valid_output"):
            raise ValueError(f"Invalid public apply result at input {index}")
        authoritative.append({"input": inputs[index], "output": row["output"]})
        output_hashes.append(grid_hash(row["output"]))
    records = prepared["records"]
    inventory = prepared["inventory"]
    predictions = prepared["predictions"]
    matches = [{rival["id"]: predicted[rival["id"]]["sha256_probe"] == output_hash
                for rival in inventory}
               for predicted, output_hash in zip(predictions, output_hashes)]
    canonical_indices = [row["index"] for row in records if row["kind"] == "canonical"]
    generated_indices = [row["index"] for row in records if row["kind"] == "generated_representative"]
    canonical_output_mismatches = [i for i in canonical_indices
                                   if output_hashes[i] != records[i]["canonical_output_sha256_probe"]]
    shortcut_results = []
    for rival in inventory:
        if not any(binding.startswith("CANONICAL_SHORTCUTS:") for binding in rival["bindings"]):
            continue
        rid = rival["id"]
        shortcut_results.append({
            **rival, "canonical_checked": len(canonical_indices),
            "canonical_mismatches": [i for i in canonical_indices if not matches[i][rid]],
            "generated_counterexamples": [i for i in generated_indices if not matches[i][rid]],
        })

    def outcomes(demos, query):
        return {rival["id"]: "refuted" if any(not matches[index][rival["id"]] for index in demos)
                else "survived_all" if matches[query][rival["id"]] else "ambiguous"
                for rival in inventory}

    windows = []
    for window in prepared["windows"]:
        indices = window["representative_indices"]
        rotations = []
        for heldout in range(len(indices)):
            query = indices[heldout]
            demos = [index for position, index in enumerate(indices) if position != heldout]
            pairs, query_pair = [deepcopy(authoritative[index]) for index in demos], deepcopy(authoritative[query])
            before_pairs, before_query = deepcopy(pairs), deepcopy(query_pair)
            reasons = gen.lesson_identifiable(pairs, query_pair)
            if pairs != before_pairs or query_pair != before_query:
                raise ValueError("Lesson hook mutated its input")
            if not isinstance(reasons, list) or any(not isinstance(reason, str) for reason in reasons):
                raise TypeError("Lesson hook must return a list of reason strings")
            rotations.append({"heldout": heldout, "query_representative": query,
                              "hook_reasons": reasons, "rivals": outcomes(demos, query)})
        windows.append({**window, "rotations": rotations})

    # Reproduce the specific old four-demo counterexample using the surviving
    # profile controls. This is intentionally distinct from the current policy.
    names = ("deep_lexicographic_tie", "branchy_unique_longest",
             "longest_over_priority", "tie_right_over_down", "tie_down_over_left")
    representatives = prepared["representatives"]
    old_counterexample = None
    if all(name in representatives for name in names):
        indices = [representatives[name] for name in names]
        old_counterexample = {
            "scope": "Old four-demo profile sequence, scored against current declarations; not a current production lesson",
            "profiles": names, "representative_indices": indices,
            "rivals": outcomes(indices[:4], indices[4]),
        }
    rotations = [rotation for window in windows for rotation in window["rotations"]]
    summary = {
        "unique_inputs": len(inputs), "canonical_pairs": len(canonical_indices),
        "generated_representatives": len(generated_indices),
        "unique_rivals": len(inventory),
        "declaration_bindings": sum(len(row["bindings"]) for row in inventory),
        "canonical_output_mismatches": len(canonical_output_mismatches),
        "invalid_inputs": sum(bool(row["self_check"]) or bool(row["strict_canonical_like"])
                              for row in records),
        "invalid_canonical_shortcuts": sum(bool(row["canonical_mismatches"]) for row in shortcut_results),
        "shortcuts_without_generated_counterexample": sum(not row["generated_counterexamples"] for row in shortcut_results),
        "cyclic_windows": len(windows), "query_rotations": len(rotations),
        "hook_warning_rotations": sum(bool(row["hook_reasons"]) for row in rotations),
        "ambiguous_rotations": sum("ambiguous" in row["rivals"].values() for row in rotations),
    }
    write_json(out / "scored.json", {
        "schema": "a55c1997c5e3-path-representatives-scored-v1",
        "scope": "All declared rivals on authoritative representative shapes and their symbolic cyclic windows",
        "task_id": TASK, "generator_sha256": current_sha,
        "probe_sha256": file_hash(Path(__file__)), "prepared_sha256": file_hash(out / "prepared.json"),
        "racket_receipt_sha256": file_hash(out / "racket.json"),
        "rule_text_sha256": receipt["rule_text_sha256"], "executed_rule_hash": receipt["executed_rule_hash"],
        "summary": summary, "inventory": inventory,
        "canonical_output_mismatches": canonical_output_mismatches,
        "canonical_shortcuts": shortcut_results, "windows": windows,
        "old_four_demo_counterexample": old_counterexample,
        "limits": [
            "Each profile reuses one labeled representative; overlapping windows are not independent generated lessons.",
            "This does not inspect retries or accepted sample indices and cannot replace production lesson-census evidence.",
            "Results cover the current finite declared rival inventory, not universal identifiability or training admission.",
        ],
    })
    print(json.dumps(summary))
    if any(summary[key] for key in ("canonical_output_mismatches", "invalid_inputs", "invalid_canonical_shortcuts",
                                   "shortcuts_without_generated_counterexample", "hook_warning_rotations",
                                   "ambiguous_rotations")):
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "apply", "score"))
    parser.add_argument("--out", type=Path, required=True, help="A new directory for prepare; the retained directory thereafter")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"), default="medium")
    parser.add_argument("--grid-h", type=int, default=16)
    parser.add_argument("--grid-w", type=int, default=18)
    args = parser.parse_args()
    if not 0 <= args.seed <= 0xFFFFFFFF:
        parser.error("seed must be a uint32")
    root = bootstrap()
    {"prepare": prepare, "apply": apply, "score": score}[args.stage](args, root)


if __name__ == "__main__":
    main()
