"""Replay a source-pinned generator census without overwriting prior evidence.

Run through the packet's run_with_racket.py wrapper. --generator and --out-dir
are required. Aggregate labels use the independent audit outline; the separate
public apply calibration retains authoritative Racket labels.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
REVIEW = HERE.parent
ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "shared/runtime"))


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


audit = load_module("independent_baseline_audit", REVIEW / "probe.py")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def grid_key(grid):
    return tuple(tuple(row) for row in grid)


def write_new(path, obj):
    with Path(path).open("x") as handle:
        json.dump(obj, handle, indent=2)
        handle.write("\n")


def geometry(grid):
    objects = audit.components(grid)
    owners = {cell: index for index, (_, cells) in enumerate(objects) for cell in cells}
    contacts = Counter()
    all_cells = set(owners)
    for (r, c), owner in owners.items():
        for dr, dc, name in ((0, 1, "horizontal"), (1, 0, "vertical"),
                             (1, 1, "down_right"), (1, -1, "down_left")):
            other = owners.get((r + dr, c + dc))
            if other is None or owner == other:
                continue
            same_color = objects[owner][0] == objects[other][0]
            if abs(dr) + abs(dc) == 1 and not same_color:
                contacts["different_color_orthogonal:" + name] += 1
            if abs(dr) + abs(dc) == 2 and same_color:
                contacts["same_color_diagonal:" + name] += 1
    bbox_h = max(r for r, c in all_cells) - min(r for r, c in all_cells) + 1
    bbox_w = max(c for r, c in all_cells) - min(c for r, c in all_cells) + 1
    return {"contacts": dict(contacts), "n_components": len(objects),
            "foreground_bbox": [bbox_h, bbox_w],
            "joint_morphology": audit.morphology(grid)}


def declarations(gen):
    result = {}
    for namespace in ("SEMANTIC_RIVALS", "LESSON_COMPETITORS", "CANONICAL_SHORTCUTS"):
        entries = getattr(gen, namespace, {})
        if not isinstance(entries, dict):
            raise TypeError(namespace + " must be a dictionary")
        for name, function in entries.items():
            if not isinstance(name, str) or not callable(function):
                raise TypeError(namespace + " has a non-callable or unnamed entry")
            result[namespace + ":" + name] = function
    return result


def compare_outputs(grid, expected, declared):
    cache, matches, errors = {}, {}, {}
    for name, function in declared.items():
        key = id(function)
        if key not in cache:
            try:
                cache[key] = (function(deepcopy(grid)), None)
            except Exception as error:
                cache[key] = (None, type(error).__name__ + ": " + str(error))
        output, error = cache[key]
        if error is not None:
            errors[name] = error
        else:
            matches[name] = output == expected
    independent = audit.rivals(grid)
    crosschecks = {}
    mapping = {"same_color_8_connected": "same_color_8_connected",
               "color_blind_4_connected_first_color": "color_blind_4_connected"}
    for name, output in independent.items():
        declared_name = "SEMANTIC_RIVALS:" + mapping[name]
        if declared_name in declared:
            declared_output, error = cache[id(declared[declared_name])]
            crosschecks[name] = error is None and output == declared_output
    return matches, errors, {name: output == expected for name, output in independent.items()}, crosschecks


def tags(grid, meta):
    facts = geometry(grid)
    tagset = {"dims:" + str((len(grid), len(grid[0]))),
              "n:" + str(facts["n_components"]),
              "morph:" + str(facts["joint_morphology"])}
    tagset.update("contact:" + key for key in facts["contacts"])
    for axis, value in meta.get("overrides", {}).items():
        tagset.add(axis + ":" + str(value))
    return tagset


def run(args):
    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    for name in ("result.json", "reviewed_generator.py", "inputs.json", "input_metadata.json"):
        if (out / name).exists():
            raise FileExistsError("Choose a new --out-dir; refusing to replace " + str(out / name))
    source = args.generator.resolve()
    snapshot = out / "reviewed_generator.py"
    snapshot.write_bytes(source.read_bytes())
    gen = load_module("selected_final_generator", snapshot)
    declared = declarations(gen)
    names = tuple(declared)
    by_band, retained, retained_meta = {}, [], []
    errors, crosscheck_failures, self_check_errors = [], [], []

    def retain(grid, meta):
        retained.append(grid)
        retained_meta.append({"input_index": len(retained) - 1, **meta,
                              "geometry": geometry(grid)})

    for band_i, band in enumerate(("easy", "medium", "hard")):
        input_counts = {name: Counter({"matches": 0, "discriminators": 0}) for name in names}
        survival = Counter({name: 0 for name in names})
        independent_counts = {name: Counter({"matches": 0, "discriminators": 0}) for name in audit.rivals([[1]])}
        independent_survival = Counter({name: 0 for name in independent_counts})
        unique_in, unique_out, base_in, base_out = set(), set(), set(), set()
        per_profile = defaultdict(lambda: {"count": 0, "inputs": set(), "outputs": set()})
        contact_inputs, contact_edges = Counter(), Counter()
        foreground_boxes, joint_morphologies = Counter(), Counter()
        canonical_strict, required_contact_errors = 0, []
        for repetition in range(1000):
            seed = 810_000 + 10_000 * band_i + repetition
            window_survives = {name: True for name in names}
            independent_window = {name: True for name in independent_counts}
            for slot in range(4):
                index = 4 * repetition + slot
                grid = gen.generate(seed, index, difficulty=band)
                structural = gen.self_check(grid)
                if structural:
                    self_check_errors.append({"seed": seed, "sample_index": index, "difficulty": band, "errors": structural})
                expected = audit.outline(grid, audit.components(grid))
                unique_in.add(grid_key(grid)); unique_out.add(grid_key(expected))
                base = audit.gen.generate(seed, index, difficulty=band)
                base_expected = audit.outline(base, audit.components(base))
                base_in.add(grid_key(base)); base_out.add(grid_key(base_expected))
                profile = str((len(grid), len(grid[0])))
                per_profile[profile]["count"] += 1
                per_profile[profile]["inputs"].add(grid_key(grid))
                per_profile[profile]["outputs"].add(grid_key(expected))
                facts = geometry(grid)
                contact_inputs.update(facts["contacts"].keys())
                contact_edges.update(facts["contacts"])
                foreground_boxes[str((facts["n_components"], *facts["foreground_bbox"]))] += 1
                joint_morphologies[str(facts["joint_morphology"])] += 1
                canonical_strict += gen.strict_canonical_like(grid) == []
                if slot in (1, 3) and not any(key.startswith("different_color_orthogonal:") for key in facts["contacts"]):
                    required_contact_errors.append({"seed": seed, "sample_index": index, "missing": "orthogonal_different_color"})
                if slot == 3 and not any(key.startswith("same_color_diagonal:") for key in facts["contacts"]):
                    required_contact_errors.append({"seed": seed, "sample_index": index, "missing": "diagonal_same_color"})
                matches, rival_errors, independent, crosschecks = compare_outputs(grid, expected, declared)
                if rival_errors:
                    errors.append({"seed": seed, "sample_index": index, "difficulty": band, "errors": rival_errors})
                if not all(crosschecks.values()):
                    crosscheck_failures.append({"seed": seed, "sample_index": index, "difficulty": band, "results": crosschecks})
                for name in names:
                    matched = matches.get(name, False)
                    input_counts[name]["matches" if matched else "discriminators"] += 1
                    window_survives[name] &= matched
                for name, matched in independent.items():
                    independent_counts[name]["matches" if matched else "discriminators"] += 1
                    independent_window[name] &= matched
                if repetition < 3:
                    retain(grid, {"kind": "natural", "seed": seed, "sample_index": index, "difficulty": band})
            survival.update(name for name, alive in window_survives.items() if alive)
            independent_survival.update(name for name, alive in independent_window.items() if alive)
        by_band[band] = {
            "inputs": 4000, "four_demo_windows": 1000,
            "declared_rival_input_counts": input_counts, "declared_rival_window_survivals": survival,
            "independent_rival_input_counts": independent_counts, "independent_rival_window_survivals": independent_survival,
            "unique_inputs": len(unique_in), "unique_outputs": len(unique_out),
            "baseline_unique_inputs_same_population": len(base_in), "baseline_unique_outputs_same_population": len(base_out),
            "per_scene_profile": {profile: {"count": data["count"], "unique_inputs": len(data["inputs"]), "unique_outputs": len(data["outputs"])} for profile, data in per_profile.items()},
            "contact_input_counts": contact_inputs, "contact_edge_counts": contact_edges,
            "foreground_bbox_counts_by_component_count": foreground_boxes,
            "joint_morphology_counts": joint_morphologies,
            "strict_canonical_count": canonical_strict, "strict_fraction": canonical_strict / 4000,
            "required_contact_errors": required_contact_errors,
        }
        print(json.dumps({"completed_band": band, "unique_inputs": len(unique_in),
                          "independent_window_survivals": independent_survival,
                          "required_contact_errors": len(required_contact_errors)}), flush=True)

    exact_lessons = []
    for old in json.loads((REVIEW / "lesson_meta.json").read_text()):
        seed, band = old["seed"], old["difficulty"]
        indexes = old["demo_indexes"] + [old["query_index"]]
        pairs, refs = [], []
        for index in indexes:
            grid = gen.generate(seed, index, difficulty=band)
            pairs.append({"input": grid, "output": audit.outline(grid, audit.components(grid))})
            refs.append(len(retained))
            retain(grid, {"kind": "former_ambiguous_lesson", "seed": seed, "sample_index": index, "difficulty": band})
        independent_fit = {name: all(audit.rivals(pair["input"])[name] == pair["output"] for pair in pairs[:4]) for name in audit.rivals(pairs[0]["input"])}
        exact_lessons.append({"seed": seed, "difficulty": band, "demo_indexes": indexes[:4], "query_index": indexes[4],
                              "reference_result_indexes": refs, "independent_rivals_fit_all_demos": independent_fit,
                              "lesson_hook_errors": gen.lesson_identifiable(pairs[:4], pairs[4])})

    override_counts = {name: Counter({"matches": 0, "discriminators": 0}) for name in names}
    override_candidates, override_errors = [], []
    domains = (("canonical_7", "canonical_9", "wide_9x13", "tall_13x9"),
               (2, 3, 4), ("distinct", "one_repeat"), ("interior", "touching"), ("low", "high", "mixed"))
    for i, values in enumerate(itertools.product(*domains)):
        ov = dict(zip(("scene_profile", "n_blobs", "color_relation", "edge_mode", "palette_kind"), values))
        grid = gen.generate(930_000 + i, i, difficulty="hard", **ov)
        structural = gen.self_check(grid, meta={"overrides": ov})
        if structural or gen.observe_overrides(grid) != ov:
            override_errors.append({"overrides": ov, "errors": structural, "observed": gen.observe_overrides(grid)})
        expected = audit.outline(grid, audit.components(grid))
        matches, rival_errors, independent, crosschecks = compare_outputs(grid, expected, declared)
        for name in names:
            override_counts[name]["matches" if matches.get(name, False) else "discriminators"] += 1
        if rival_errors or not all(crosschecks.values()):
            override_errors.append({"overrides": ov, "rival_errors": rival_errors, "crosschecks": crosschecks})
        meta = {"kind": "override", "seed": 930_000 + i, "sample_index": i, "difficulty": "hard", "overrides": ov}
        override_candidates.append((grid, meta, tags(grid, meta)))
    covered = set().union(*(tags(grid, meta) for grid, meta in zip(retained, retained_meta)))
    while len(retained) < 64 and override_candidates:
        choice = max(range(len(override_candidates)), key=lambda i: len(override_candidates[i][2] - covered))
        grid, meta, features = override_candidates.pop(choice)
        retain(grid, meta)
        covered.update(features)

    result = {
        "schema": "cc8c719680e6-independent-final-census-v1", "task_id": gen.TASK_ID, "version": gen.VERSION,
        "generator_source": str(source), "generator_sha256": digest(snapshot),
        "baseline_generator_sha256": digest(REVIEW / "baseline_generator.py"),
        "probe_sha256": digest(__file__), "independent_helpers_sha256": digest(REVIEW / "probe.py"),
        "rule_pin": gen.RULE_HASH,
        "command": ["python3", *sys.argv], "cwd": str(Path.cwd()),
        "population": {"bands": ["easy", "medium", "hard"], "windows_per_band": 1000,
                       "seed": "810000 + 10000 * band_index + repetition", "indices": "4 * repetition through 4 * repetition + 3"},
        "label_basis": "Independent Python outline for aggregate counts; inputs.json is the <=64-input public apply calibration. No aggregate Python labels are retained.",
        "declared_rivals": {name: function.__name__ for name, function in declared.items()},
        "by_band": by_band, "self_check_errors": self_check_errors,
        "declared_rival_errors": errors, "independent_declared_crosscheck_failures": crosscheck_failures,
        "exact_formerly_ambiguous_lessons": exact_lessons,
        "override_census": {"inputs": 144, "rival_counts": override_counts, "errors": override_errors},
        "retained_reference_inputs": len(retained), "retained_features": sorted(covered),
        "selected_source_unchanged_after_census": digest(source) == digest(snapshot),
    }
    write_new(out / "inputs.json", {"inputs": retained})
    write_new(out / "input_metadata.json", retained_meta)
    write_new(out / "result.json", result)
    print(json.dumps({"result": str(out / "result.json"), "source_sha256": result["generator_sha256"],
                      "declarations": len(declared), "reference_inputs": len(retained),
                      "errors": len(errors) + len(crosscheck_failures) + len(self_check_errors) + len(override_errors)}, indent=2))


def verify(args):
    out = args.out_dir.resolve()
    result = json.loads((out / "result.json").read_text())
    receipt = json.loads((out / "racket.json").read_text())
    inputs = json.loads((out / "inputs.json").read_text())["inputs"]
    meta = json.loads((out / "input_metadata.json").read_text())
    gen = load_module("calibrated_final_generator", out / "reviewed_generator.py")
    declared = declarations(gen)
    assert receipt["executed_rule_hash"] == result["rule_pin"]
    assert len(receipt["results"]) == len(inputs) == len(meta)
    rows, failures = [], []
    for index, record in enumerate(receipt["results"]):
        assert record["input"] == inputs[index]
        if record["error"] is not None or not record["valid_output"]:
            failures.append({"input_index": index, "error": record["error"]})
            continue
        expected, grid = record["output"], record["input"]
        independent_match = audit.outline(grid, audit.components(grid)) == expected
        matches, errors, independent, crosschecks = compare_outputs(grid, expected, declared)
        if not independent_match or errors or not all(crosschecks.values()):
            failures.append({"input_index": index, "independent_match": independent_match, "errors": errors, "crosschecks": crosschecks})
        rows.append({"input_index": index, "kind": meta[index]["kind"], "independent_outline_matches_racket": independent_match,
                     "declared_rivals_match_racket": matches, "independent_rivals_match_racket": independent})
    lessons = []
    for old in result["exact_formerly_ambiguous_lessons"]:
        pairs = [receipt["results"][index] for index in old["reference_result_indexes"]]
        lessons.append({**old, "lesson_hook_errors_using_racket_labels": gen.lesson_identifiable(pairs[:4], pairs[4]),
                        "declared_rivals_fit_all_racket_demos": {name: all(function(deepcopy(pair["input"])) == pair["output"] for pair in pairs[:4]) for name, function in declared.items()}})
    verification = {"generator_sha256": result["generator_sha256"], "executed_rule_hash": receipt["executed_rule_hash"],
                    "apply_generator_sha256": receipt["generator_sha256"], "racket_receipt_sha256": digest(out / "racket.json"),
                    "results": len(rows), "failures": failures, "rows": rows, "exact_lessons": lessons,
                    "command": ["python3", *sys.argv], "cwd": str(Path.cwd())}
    write_new(out / "reference_verification.json", verification)
    print(json.dumps({"generator_sha256": result["generator_sha256"], "racket_results": len(rows), "failures": failures,
                      "lesson_hook_errors": [lesson["lesson_hook_errors_using_racket_labels"] for lesson in lessons]}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--verify-reference", action="store_true")
    arguments = parser.parse_args()
    if arguments.verify_reference:
        verify(arguments)
    else:
        run(arguments)
