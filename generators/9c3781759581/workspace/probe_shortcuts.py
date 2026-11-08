#!/usr/bin/env python3
"""Check the selected generator's declared rivals against real Racket labels.

Run through WORK/run_with_racket.py with --out pointing to a new report file.
The bounded cohort is three canonical pairs, 36 default generated inputs
(seed 17, indexes 0..11, easy/medium/hard), and one small lawful witness.
No generator, rule, test, catalog, approval, or solve-lane file is changed.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root, load_selected_generator, normalize_grid


TASK_ID = "9c3781759581"
EXPECTED_GENERATOR_SHA256 = "dc6d9c68d1fb740b525c19716e9766060b8bf959585dcfd49b6634b08ebc9876"
DIFFICULTIES = ("easy", "medium", "hard")
REGISTRY_NAMES = ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS")
SMALL_WITNESS = [[2, 0, 0, 2], [0, 9, 9, 0], [0, 9, 0, 0]]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_inputs(generator, root: Path) -> list[dict]:
    pairs = canonical_pairs(TASK_ID, root=root)
    if len(pairs) != 3:
        raise ValueError(f"Expected all three canonical pairs, found {len(pairs)}")
    inputs = []
    for pair in pairs:
        inputs.append({
            "input_id": f"canonical-v{pair['variant']}-{pair['split']}-{pair['pair_index']}",
            "kind": "canonical", "seed": None, "sample_index": None,
            "difficulty": None, "overrides": None,
            "canonical_identity": {key: pair[key] for key in ("variant", "split", "pair_index")},
            "input": pair["input"], "recorded_canonical_output": pair["output"],
        })
    for difficulty in DIFFICULTIES:
        for index in range(12):
            inputs.append({
                "input_id": f"generated-{difficulty}-s17-i{index}",
                "kind": "generated", "seed": 17, "sample_index": index,
                "difficulty": difficulty, "overrides": {},
                "input": generator.generate(17, index, difficulty=difficulty),
            })
    inputs.append({
        "input_id": "small-lawful-witness", "kind": "supplemental",
        "seed": None, "sample_index": None, "difficulty": None, "overrides": None,
        "origin": "hand-constructed", "input": copy.deepcopy(SMALL_WITNESS),
    })
    if len(inputs) != 40:
        raise AssertionError("The declared cohort must contain exactly 40 inputs")
    return inputs


def assess_registry(name: str, registry: dict, inputs: list[dict]) -> tuple[dict, list[str]]:
    """Use the live declarations; exceptions never count as rival refutations."""
    results = {}
    failures = []
    for rival_name, rival in registry.items():
        fit = {kind: {"matches": 0, "total": 0, "errors": 0}
               for kind in ("canonical", "generated", "supplemental")}
        refuting_ids = {kind: [] for kind in fit}
        execution_errors = []
        first_generated = None
        supplemental_prediction = None
        for instance in inputs:
            kind = instance["kind"]
            fit[kind]["total"] += 1
            try:
                prediction = normalize_grid(rival(copy.deepcopy(instance["input"])))
            except Exception as error:
                fit[kind]["errors"] += 1
                execution_errors.append({"input_id": instance["input_id"],
                                         "error_type": type(error).__name__, "error": str(error)})
                continue
            matches = prediction == instance["output"]
            fit[kind]["matches"] += int(matches)
            if not matches:
                refuting_ids[kind].append(instance["input_id"])
                if kind == "generated" and first_generated is None:
                    first_generated = {
                        key: copy.deepcopy(instance[key])
                        for key in ("input_id", "seed", "sample_index", "difficulty",
                                    "overrides", "input", "output", "input_sha256", "output_sha256")
                    }
                    first_generated["rival_output"] = prediction
                    first_generated["generator_domain"] = instance["generator_domain"]
            if kind == "supplemental":
                supplemental_prediction = {"input_id": instance["input_id"],
                                           "output": prediction, "matches_reference": matches}
        canonical_claim_ok = (fit["canonical"]["matches"] == 3
                              and fit["canonical"]["errors"] == 0)
        generated_refutation_ok = first_generated is not None
        if execution_errors:
            failures.append(f"{name}.{rival_name}: rival execution errors")
        if name == "CANONICAL_SHORTCUTS" and not canonical_claim_ok:
            failures.append(f"{name}.{rival_name}: claimed canonical shortcut does not fit all three pairs")
        if not generated_refutation_ok:
            failures.append(f"{name}.{rival_name}: no generated Racket-refuting witness in the cohort")
        results[rival_name] = {
            "callable_name": getattr(rival, "__name__", type(rival).__name__),
            "fit_counts": fit,
            "canonical_shortcut_claim_required": name == "CANONICAL_SHORTCUTS",
            "fits_all_canonical_pairs": canonical_claim_ok,
            "has_generated_reference_refutation": generated_refutation_ok,
            "refuting_input_ids": refuting_ids,
            "first_generated_refuting_witness": first_generated,
            "supplemental_prediction": supplemental_prediction,
            "execution_errors": execution_errors,
        }
    return results, failures


def run(out: Path) -> dict:
    root = find_root(__file__)
    out = out.expanduser().absolute()
    if out.exists():
        raise FileExistsError(f"Report path must be new: {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "schema": "marker-crop-declared-shortcut-probe-v1", "status": "running",
        "task_id": TASK_ID,
        "invocation": {"cwd": str(Path.cwd()), "argv": list(sys.argv),
                       "python_executable": sys.executable, "python_version": sys.version},
        "probe_sha256": sha256(Path(__file__)),
        "scope": {"canonical_pairs": 3, "generated_inputs": 36, "supplemental_inputs": 1,
                  "total_reference_inputs": 40, "generated_seed": 17,
                  "generated_sample_indexes": list(range(12)),
                  "generated_difficulties": list(DIFFICULTIES), "generated_overrides": {}},
        "limitations": [
            "This is a finite input-level probe of the current CANONICAL_SHORTCUTS and LESSON_COMPETITORS declarations, not arbitrary unlisted hypotheses.",
            "All 40 retained outputs are actual canonical Racket results; rival outputs are the declared Python callbacks.",
            "Generated refutations must come from the 36 specified draws; the hand-constructed witness cannot satisfy that requirement.",
            "This probe does not assemble lessons, test query rotations, estimate unseen-seed coverage, or grant approval.",
            "The source-hash guard binds this retained probe to the final v3.0.2 review source; update the guard deliberately when auditing changed source.",
        ],
        "failures": [],
    }
    # Exclusive creation reserves the fresh path and leaves a visible receipt
    # if validation or the reference runtime subsequently fails.
    with out.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    try:
        generator, source, source_hash = load_selected_generator(TASK_ID, root=root)
        report["generator"] = {"path": source.relative_to(root).as_posix(),
                               "version": generator.VERSION, "sha256": source_hash}
        if source_hash != EXPECTED_GENERATOR_SHA256:
            raise RuntimeError(f"Selected source differs from the frozen review source: {source_hash}")
        registries = {}
        for name in REGISTRY_NAMES:
            registry = getattr(generator, name, None)
            if not isinstance(registry, dict) or not registry:
                raise ValueError(f"{name} must be a nonempty declared mapping")
            if any(not isinstance(key, str) or not key or not callable(value)
                   for key, value in registry.items()):
                raise ValueError(f"{name} must map nonempty rival names to callables")
            registries[name] = dict(registry)
        report["declarations"] = {name: list(registry) for name, registry in registries.items()}
        inputs = build_inputs(generator, root)
        report["inputs"] = inputs
        for instance in inputs:
            instance["self_check"] = generator.self_check(instance["input"])
            if instance["self_check"]:
                report["failures"].append(f"{instance['input_id']}: self_check rejects input")

        applied = Catalog(root).apply(
            TASK_ID, [instance["input"] for instance in inputs], reference="canonical",
            allow_unapproved=True, check_generator_domain=True, timeout=120,
        )
        report["reference"] = {key: copy.deepcopy(value) for key, value in applied.items()
                               if key != "results"}
        if applied["generator_sha256"] != source_hash:
            raise RuntimeError("Racket execution used different generator source")
        if not applied["rule_hash_matches_catalog"] or applied["executed_rule_hash"] != generator.RULE_HASH:
            raise RuntimeError("Executed rule differs from the declared selected canonical rule")
        if len(applied["results"]) != 40:
            raise RuntimeError("Racket did not return all 40 results")
        for instance, actual in zip(inputs, applied["results"], strict=True):
            if actual["input"] != instance["input"]:
                raise RuntimeError("Racket result input order does not match the submitted cohort")
            instance.update(copy.deepcopy(actual))
            domain = instance.get("generator_domain", {})
            if domain.get("status") != "valid" or domain.get("errors"):
                report["failures"].append(f"{instance['input_id']}: public generator-domain check is not valid")
            normalize_grid(instance["output"])
            if instance["kind"] == "canonical" and instance["output"] != instance["recorded_canonical_output"]:
                report["failures"].append(f"{instance['input_id']}: Racket disagrees with recorded canonical label")

        report["rivals"] = {}
        for name, registry in registries.items():
            results, failures = assess_registry(name, registry, inputs)
            report["rivals"][name] = results
            report["failures"].extend(failures)
        if sha256(source) != source_hash:
            raise RuntimeError("Generator changed during the probe")
        report["generator_unchanged_during_probe"] = True
        all_results = [row for registry in report["rivals"].values() for row in registry.values()]
        report["summary"] = {
            "canonical_inputs_checked": 3, "generated_inputs_checked": 36,
            "supplemental_inputs_checked": 1, "actual_racket_inputs_checked": 40,
            "domain_errors": sum(bool(instance["self_check"]) or
                                 instance.get("generator_domain", {}).get("status") != "valid" or
                                 bool(instance.get("generator_domain", {}).get("errors"))
                                 for instance in inputs),
            "canonical_shortcut_claims": len(registries["CANONICAL_SHORTCUTS"]),
            "canonical_shortcuts_fitting_all_three": sum(
                row["fits_all_canonical_pairs"]
                for row in report["rivals"]["CANONICAL_SHORTCUTS"].values()),
            "declared_lesson_competitors": len(registries["LESSON_COMPETITORS"]),
            "registry_entries_checked": len(all_results),
            "unique_rival_names": len(set().union(*(registry.keys() for registry in registries.values()))),
            "registry_entries_with_generated_refutation": sum(
                row["has_generated_reference_refutation"] for row in all_results),
            "rival_execution_errors": sum(len(row["execution_errors"]) for row in all_results),
        }
        report["status"] = "pass" if not report["failures"] else "fail"
    except Exception as error:
        report["status"] = "error"
        report["error"] = {"type": type(error).__name__, "message": str(error)}
    out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="New JSON report path; existing paths are refused")
    args = parser.parse_args(argv)
    try:
        report = run(args.out)
    except (FileExistsError, OSError, ValueError) as error:
        print(json.dumps({"status": "error", "error": str(error)}), file=sys.stderr)
        return 2
    print(json.dumps({"status": report["status"], "report": str(args.out),
                      "generator": report.get("generator"), "summary": report.get("summary"),
                      "failures": report["failures"], "error": report.get("error")}, indent=2))
    return 0 if report["status"] == "pass" else 1 if report["status"] == "fail" else 2


if __name__ == "__main__":
    raise SystemExit(main())
