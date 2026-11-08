#!/usr/bin/env python3
"""Finite, task-local Python-mirror diagnostics; never an output-authority gate.

From a library packet::

    python3 run_with_racket.py python3 generators/31e43af4bcfa/workspace/probe_curriculum.py --out ../checks/probe-final.json

The same file runs in a copied runtime, with --root /explicit/runtime if needed.
Default cyclic starts cover the three teaching profiles. --starts 24 covers the
combined phase period of profile scheduling (3) and dimension anchors (8).
Only public reviewer_support and the selected generator's normal runtime imports
are used. No reference execution, private scripts, or solve artifacts are read.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys
import traceback


TASK = "31e43af4bcfa"
NAMESPACES = ("LESSON_COMPETITORS", "SEMANTIC_RIVALS", "CANONICAL_SHORTCUTS")
BANDS = (None, "easy", "medium", "hard")


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha_json(value):
    return sha_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def bootstrap(explicit_root):
    candidates = [Path(explicit_root).resolve()] if explicit_root else list(Path(__file__).resolve().parents)
    for candidate in candidates:
        support = next((candidate / relative for relative in
                        ("reviewer_support.py", "shared/runtime/reviewer_support.py")
                        if (candidate / relative).is_file()), None)
        if support:
            public = load_module("reviewer_support", support)
            root = public.find_root(candidate)
            if explicit_root and root != candidate:
                raise ValueError("--root must identify the library/runtime root itself")
            runtime = root / "shared/runtime" if (root / "shared/runtime").is_dir() else root
            sys.path.insert(0, str(runtime))
            source = next((root / relative for relative in
                           (f"generators/{TASK}/generator.py",
                            f"puzzle_generators/per_puzzle/{TASK}/generator.py")
                           if (root / relative).is_file()), None)
            if source is None:
                raise FileNotFoundError(f"No selected generator for {TASK} under {root}")
            return root, source, public
    raise FileNotFoundError("No library/runtime root found; pass --root explicitly")


def row_list_ids(grid):
    return {id(grid), *(id(row) for row in grid)}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", help="Explicit library or copied runtime root (otherwise find from this file)")
    parser.add_argument("--out", required=True, type=Path, help="New JSON evidence path; never overwrite")
    parser.add_argument("--seeds", type=int, default=5, help="Default-lesson seeds 0..N-1 (default 5)")
    parser.add_argument("--starts", type=int, help="Consecutive cyclic lesson starts (default profile count; 24 covers profile3/anchor8)")
    parser.add_argument("--override-seed", type=int, default=17, help="Replay seed for the complete joint override census")
    args = parser.parse_args()
    if args.seeds < 1:
        parser.error("--seeds must be positive")
    if args.starts is not None and args.starts < 1:
        parser.error("--starts must be positive")
    out = args.out.resolve()
    if out.exists():
        parser.error(f"Output already exists: {out}")
    report = {"schema": "31e43af4bcfa-python-mirror-probe-v1", "task_id": TASK,
              "label_basis": "Python-mirror diagnostic; generated outputs are not Racket labels",
              "scope": "Finite checks of selected declarations; no proof of universal identifiability or approval change",
              "configuration": {"lesson_seeds": list(range(args.seeds)), "override_seed": args.override_seed,
                                "bands": list(BANDS), "override_residues": [0, 1, 2]},
              "failures": [], "first_witnesses": {}, "first_rival_refutations": {}}
    counts = Counter()

    def fail(kind, context, **detail):
        report["failures"].append({"kind": kind, **deepcopy(context), **detail})

    try:
        root, source, public = bootstrap(args.root)
        source_bytes = source.read_bytes()
        gen = load_module("curriculum_probe_selected_generator", source)
        ledger = next(root / relative for relative in
                      ("data/canonical/puzzles.jsonl", "shared/data/canonical/puzzles.jsonl")
                      if (root / relative).is_file())
        pairs = public.canonical_pairs(TASK, root=root, labeled_only=True)
        if not pairs:
            raise ValueError("No usable canonical labeled pairs")
        report["binding"] = {"root": str(root), "generator_path": str(source.relative_to(root)),
                             "generator_sha256": sha_bytes(source_bytes), "version": gen.VERSION,
                             "canonical_ledger_sha256": sha_bytes(ledger.read_bytes()),
                             "canonical_pairs_sha256": sha_json(pairs),
                             "canonical_pair_count": len(pairs)}
        report["canonical_pairs"] = [{**pair, "pair_sha256": sha_json(pair)} for pair in pairs]
        rivals = {}
        declarations = {}
        for namespace in NAMESPACES:
            declaration = getattr(gen, namespace, None)
            if not isinstance(declaration, dict) or not declaration:
                fail("invalid_rival_declaration", {}, namespace=namespace)
                continue
            declarations[namespace] = list(declaration)
            for name, rival in declaration.items():
                if not isinstance(name, str) or not callable(rival):
                    fail("invalid_rival", {}, namespace=namespace, name=str(name))
                    continue
                rivals[f"{namespace}.{name}"] = rival
        report["declarations"] = declarations
        witnesses = getattr(gen, "SEMANTIC_WITNESSES", {})
        witness_rivals = getattr(gen, "WITNESS_RIVALS", {})
        profiles = tuple(gen.SCHEDULE_PROFILES)
        starts = args.starts if args.starts is not None else len(profiles)
        report["configuration"].update({"schedule_profiles": list(profiles),
                                        "examples_needed": gen.EXAMPLES_NEEDED,
                                        "cyclic_starts": list(range(starts)),
                                        "combined_profile_and_dimension_anchor_period": 24})
        report["witness_rivals"] = deepcopy(witness_rivals)
        if len(profiles) != 3:
            fail("unexpected_schedule_period", {}, expected=3, actual=len(profiles))
        for name in witnesses:
            if not callable(witnesses[name]) or name not in witness_rivals or not witness_rivals[name]:
                fail("invalid_witness_declaration", {}, witness=name)
        for name, names in witness_rivals.items():
            if name not in witnesses or not isinstance(names, (list, tuple)) or not names:
                fail("invalid_witness_rivals", {}, witness=name)
                continue
            for rival_name in names:
                matches = [rival for key, rival in rivals.items() if key.split(".", 1)[1] == rival_name]
                if not matches:
                    fail("missing_named_witness_rival", {}, witness=name, rival=rival_name)
        def prediction(rival_name, grid, context):
            supplied = deepcopy(grid)
            try:
                result = rivals[rival_name](supplied)
                if supplied != grid:
                    fail("rival_mutated_input", context, rival=rival_name)
                if (not isinstance(result, list) or not result
                        or any(not isinstance(row, list) or not row for row in result)
                        or len({len(row) for row in result}) != 1
                        or any(type(value) is not int or not 0 <= value <= 9
                               for row in result for value in row)):
                    fail("invalid_rival_prediction", context, rival=rival_name,
                         prediction_repr=repr(result))
                    return None, False
                return result, True
            except Exception as exc:
                fail("rival_exception", context, rival=rival_name,
                     error=f"{type(exc).__name__}: {exc}")
                return None, False

        matrix = {}
        for rival_name in rivals:
            statuses = []
            for pair in pairs:
                context = {"stage": "canonical", "variant": pair["variant"],
                           "split": pair["split"], "pair_index": pair["pair_index"]}
                pred, ok = prediction(rival_name, pair["input"], context)
                statuses.append("fit" if ok and pred == pair["output"] else "refuted" if ok else "error")
            matrix[rival_name] = {"pair_statuses": statuses, "fits_all": all(s == "fit" for s in statuses)}
            if rival_name.startswith("CANONICAL_SHORTCUTS.") and not matrix[rival_name]["fits_all"]:
                fail("canonical_shortcut_not_fitting", {"stage": "canonical"}, rival=rival_name, statuses=statuses)
        report["canonical_fit_matrix"] = matrix
        for pair in pairs:
            context = {"stage": "canonical", "variant": pair["variant"], "split": pair["split"], "pair_index": pair["pair_index"]}
            if gen.self_check(pair["input"]):
                fail("canonical_self_check", context, errors=gen.self_check(pair["input"]))
            if gen.rule_mirror(pair["input"]) != pair["output"]:
                fail("canonical_mirror_disagreement", context)

        generated_hashes, output_hashes = set(), set()
        per_band = {str(band): Counter() for band in BANDS}
        witness_counts, refutation_counts = Counter(), Counter()

        def generated_case(seed, index, band, overrides, stage):
            context = {"stage": stage, "seed": seed, "sample_index": index,
                       "difficulty": band, "overrides": dict(overrides)}
            counts[f"{stage}_attempted"] += 1
            try:
                grid = gen.generate(seed, index, difficulty=band, **overrides)
                duplicate = gen.generate(seed, index, difficulty=band, **overrides)
                if grid != duplicate:
                    fail("nondeterministic_generation", context, input=grid, repeated_input=duplicate)
                if row_list_ids(grid) & row_list_ids(duplicate):
                    fail("nonfresh_grid_or_rows", context)
                snapshot = deepcopy(duplicate)
                grid[0][0] = -100
                if duplicate != snapshot:
                    fail("return_mutation_leaked", context)
                grid = duplicate
                errors = gen.self_check(grid, difficulty=band)
                if errors:
                    fail("generated_self_check", context, errors=errors, input=grid)
                observed = gen.observe_overrides(grid)
                if any(observed.get(key) != value for key, value in overrides.items()):
                    fail("override_observation_mismatch", context, observed=observed, input=grid)
                expected = gen.schedule_profile(seed, index, band)
                context["schedule_profile"] = expected
                if expected != profiles[index % len(profiles)]:
                    fail("schedule_residue_mismatch", context)
                output = gen.rule_mirror(deepcopy(grid))
                input_sha = sha_json(grid)
                generated_hashes.add(input_sha)
                output_hashes.add(sha_json(output))
                predictions = {}
                for name in rivals:
                    pred, ok = prediction(name, grid, context)
                    predictions[name] = (pred, ok)
                    if ok and pred != output:
                        refutation_counts[name] += 1
                        report["first_rival_refutations"].setdefault(name, {**context, "input_sha256": input_sha,
                            "input": grid, "python_mirror_output": output, "rival_prediction": pred})
                active = []
                for name, predicate in witnesses.items():
                    try:
                        if not predicate(deepcopy(grid)):
                            continue
                        active.append(name)
                        witness_counts[name] += 1
                        evidence = {**context, "input_sha256": input_sha, "input": grid,
                                    "python_mirror_output": output, "named_refutations": {}}
                        for rival_name in witness_rivals.get(name, []):
                            for key in rivals:
                                if key.split(".", 1)[1] != rival_name:
                                    continue
                                pred, ok = predictions[key]
                                if ok and pred == output:
                                    fail("claimed_witness_does_not_refute_named_rival", context,
                                         witness=name, rival=key, input=grid, python_mirror_output=output)
                                elif ok:
                                    evidence["named_refutations"][key] = pred
                        report["first_witnesses"].setdefault(name, evidence)
                    except Exception as exc:
                        fail("witness_exception", context, witness=name, error=f"{type(exc).__name__}: {exc}")
                if expected not in active:
                    fail("scheduled_witness_missing", context, active_witnesses=active, input=grid)
                counts[f"{stage}_completed"] += 1
                per_band[str(band)][expected] += 1
                return {"input": grid, "output": output, "sample_index": index}, predictions
            except Exception as exc:
                fail("generated_case_exception", context, error=f"{type(exc).__name__}: {exc}")
                return None, None

        for band, k, h, w, residue in itertools.product(BANDS, range(2, 5), range(5, 10), range(7, 14), range(3)):
            generated_case(args.override_seed, residue, band, {"K": k, "grid_h": h, "grid_w": w}, "joint_overrides")
        print("Joint override census completed (1260 requested cases).", file=sys.stderr)
        lesson_scores = {key: Counter() for key in rivals}
        for band, seed, start in itertools.product(BANDS, range(args.seeds), range(starts)):
            lesson, predictions = [], []
            for index in range(start, start + gen.EXAMPLES_NEEDED + 1):
                pair, pred = generated_case(seed, index, band, {}, "default_pairs")
                lesson.append(pair)
                predictions.append(pred)
            counts["lessons_attempted"] += 1
            if any(pair is None for pair in lesson):
                continue
            counts["lessons_completed"] += 1
            for held_out, query in enumerate(lesson):
                counts["query_holdouts"] += 1
                context = {"stage": "query_holdout", "seed": seed, "lesson_start": start,
                           "sample_index": query["sample_index"], "difficulty": band, "overrides": {},
                           "query_position": held_out,
                           "demonstration_indices": [p["sample_index"] for i, p in enumerate(lesson) if i != held_out]}
                for name in rivals:
                    values = [pred[name] for pred in predictions]
                    if not all(ok for _, ok in values):
                        lesson_scores[name]["error"] += 1
                        continue
                    fits = all(values[i][0] == pair["output"] for i, pair in enumerate(lesson) if i != held_out)
                    disagrees = values[held_out][0] != query["output"]
                    status = "ambiguous" if fits and disagrees else "survived_all" if fits else "refuted_by_demos"
                    lesson_scores[name][status] += 1
                    if status == "ambiguous":
                        fail("declared_rival_query_ambiguity", context, rival=name,
                             lesson=lesson, rival_query_prediction=values[held_out][0])
                try:
                    reasons = gen.lesson_identifiable([deepcopy(p) for i, p in enumerate(lesson) if i != held_out], deepcopy(query))
                    if reasons:
                        fail("lesson_hook_reasons", context, reasons=reasons, lesson=lesson)
                except Exception as exc:
                    fail("lesson_hook_exception", context, error=f"{type(exc).__name__}: {exc}")
        report["lesson_holdout_scores"] = {key: dict(value) for key, value in lesson_scores.items()}
        report["generated_summary"] = {"counts": dict(counts), "unique_inputs": len(generated_hashes),
            "unique_python_mirror_outputs": len(output_hashes), "per_band_schedule_counts": {key: dict(value) for key, value in per_band.items()},
            "witness_counts": dict(witness_counts), "rival_refutation_counts": dict(refutation_counts)}
        for name in witnesses:
            if not witness_counts[name]:
                fail("unobserved_declared_witness", {}, witness=name)
        for name in rivals:
            if not refutation_counts[name]:
                fail("unrefuted_declared_rival", {}, rival=name)
        local_modules = {}
        for name, module in sorted(sys.modules.items()):
            path = getattr(module, "__file__", None)
            if path and Path(path).is_file() and Path(path).resolve().is_relative_to(root):
                resolved = Path(path).resolve()
                local_modules[name] = {"path": str(resolved.relative_to(root)), "sha256": sha_bytes(resolved.read_bytes())}
        report["source_provenance"] = {"loaded_local_modules": local_modules,
            "scope": "Module hashes are provenance only; this diagnostic does not certify source isolation"}
        if source.read_bytes() != source_bytes:
            fail("source_changed_during_probe", {}, final_generator_sha256=sha_bytes(source.read_bytes()))
    except Exception as exc:
        fail("probe_exception", {}, error=f"{type(exc).__name__}: {exc}", traceback=traceback.format_exc())
    report["status"] = "defects_found" if report["failures"] else "no_defects_found_in_finite_python_mirror_probe"
    report["failure_count"] = len(report["failures"])
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({"status": report["status"], "failure_count": report["failure_count"],
                      "counts": dict(counts), "out": str(out)}, sort_keys=True))
    return 1 if report["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
