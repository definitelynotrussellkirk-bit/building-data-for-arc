#!/usr/bin/env python3
"""Racket-backed authoring probe of every cyclic start and query position.

For each requested seed/band, generate the *actual consecutive* sample indices
0..period+train-1.  Each start in 0..period-1 selects train+1 of those draws;
hold out every pair once, preserving the order of the remaining demonstrations.
Only the role schedule is cyclic: grids are never repeated by modulo indexing.

This is a direct-window diagnostic, not the production rejection sampler.
Duplicates, validation rejects, and execution errors remain attached to their
original indices; no replacement draws are substituted.  Use the shared
``arcpuzzles lesson-census --rotate-query`` for production-assembled lessons.

Runs from its own library or an apply-capable portable task-test snapshot.
A bare legacy runtime without catalog/API data fails explicitly.  No sibling
checkout, private runner, Python rule mirror, or solve answers supply labels.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib
import importlib.util
import inspect
import json
from pathlib import Path
import re
import sys


NAMESPACES = ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS", "SEMANTIC_RIVALS")
DEFAULT_TASK = "f1668de79fa1"
APPLY_BATCH_SIZE = 64


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def file_digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def grid_copy(value):
    """Strict integer grids for generated inputs and rival predictions."""
    if (not isinstance(value, list) or not 1 <= len(value) <= 30
            or not all(isinstance(row, list) and 1 <= len(row) <= 30 for row in value)
            or len({len(row) for row in value}) != 1
            or any(type(cell) is not int or not 0 <= cell <= 9 for row in value for cell in row)):
        raise ValueError("expected a rectangular 1..30 x 1..30 integer grid with colors 0..9")
    return deepcopy(value)


def evidence_value(value):
    """Retain malformed returns too, without making the report unserializable."""
    try:
        json.dumps(value, allow_nan=False)
        return deepcopy(value)
    except (TypeError, ValueError):
        return {"python_type": type(value).__name__, "repr": repr(value)}


def load_source(path, prefix):
    """Import the selected file's exact bytes, without a stale .pyc cache."""
    path = Path(path).resolve()
    name = prefix + "_" + hashlib.sha256(str(path).encode()).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


def find_tree(start):
    start = Path(start).resolve()
    if start.is_file():
        start = start.parent
    for root in (start, *start.parents):
        for relative in ("shared/data/canonical/puzzles.jsonl", "data/canonical/puzzles.jsonl"):
            if (root / relative).is_file():
                return root
    raise FileNotFoundError(f"no library/runtime canonical ledger above {start}")


def select_generator(root, task_id, row=None):
    """Resolve only inside the explicitly selected library/runtime."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", task_id):
        raise ValueError(f"invalid task ID: {task_id!r}")
    candidates = ([row["generator"], row["runtime_generator"]] if row else
                  [f"generators/{task_id}/generator.py",
                   f"puzzle_generators/per_puzzle/{task_id}/generator.py"])
    for relative in candidates:
        if not relative:
            continue
        path = (root / relative).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError(f"generator path escapes the selected tree: {relative}")
        if path.is_file():
            return path
    raise FileNotFoundError(f"no selected generator for {task_id} in {root}")


def local_environment(root):
    """Bind helper imports and Catalog to this tree, never an ambient sibling."""
    if not (root / "catalog/puzzles.jsonl").is_file():
        raise FileNotFoundError(
            "Catalog(root).apply needs this tree's catalog data; use a source library "
            "or self-contained task-test snapshot, not a bare legacy runtime")
    helper_root = root / "shared/runtime"
    if not (helper_root / "reviewer_support.py").is_file():
        helper_root = root
    support_path = helper_root / "reviewer_support.py"
    if not support_path.is_file():
        raise FileNotFoundError(f"missing portable reviewer_support.py in {root}")
    api_root = root / "src"
    for name, allowed in (("puzzle_generators", helper_root), ("arcpuzzles", api_root)):
        # An installed API is usable when a library has no source package.
        if name == "arcpuzzles" and not (api_root / "arcpuzzles").is_dir():
            continue
        for key, module in tuple(sys.modules.items()):
            location = getattr(module, "__file__", None)
            if (key == name or key.startswith(name + ".")) and location:
                if not Path(location).resolve().is_relative_to(allowed.resolve()):
                    raise ImportError(f"refusing {key} imported from outside this tree: {location}")
    sys.path.insert(0, str(helper_root))
    if (api_root / "arcpuzzles").is_dir():
        sys.path.insert(0, str(api_root))
    support = load_source(support_path, "lesson_window_support")
    if support.find_root(root) != root:
        raise RuntimeError("reviewer_support resolved a different source tree")
    helper_ledger = support.canonical_path(root)
    catalog_ledger = root / "shared/data/canonical/puzzles.jsonl"
    if helper_ledger != catalog_ledger and file_digest(helper_ledger) != file_digest(catalog_ledger):
        raise RuntimeError("portable helper and Catalog canonical ledgers differ")
    return importlib.import_module("arcpuzzles").Catalog(root), support


def declared_rivals(gen):
    rivals, declarations, errors = {}, {}, []
    for namespace in NAMESPACES:
        present = hasattr(gen, namespace)
        value = getattr(gen, namespace, None)
        declarations[namespace] = {"present": present, "names": []}
        if not present:
            continue
        if not isinstance(value, dict):
            errors.append(f"{namespace}: expected a dict of named callables")
            continue
        for name, fn in value.items():
            if not isinstance(name, str) or not name or not callable(fn):
                errors.append(f"{namespace}:{name!r}: expected nonempty string name and callable")
            else:
                rivals[f"{namespace}:{name}"] = fn
                declarations[namespace]["names"].append(name)
        declarations[namespace]["names"].sort()
    hook = getattr(gen, "lesson_identifiable", None)
    if hook is not None and not callable(hook):
        errors.append("lesson_identifiable: expected a callable")
    return rivals, declarations, errors


def prediction(name, fn, grid, cache):
    key = (name, digest(grid))
    if key not in cache:
        raw = None
        try:
            raw = fn(deepcopy(grid))
            cache[key] = {"output": grid_copy(raw), "error": None}
        except Exception as exc:
            cache[key] = {"output": None, "returned": evidence_value(raw),
                          "error": f"{type(exc).__name__}: {exc}"}
    return deepcopy(cache[key])


def score_rotations(gen, rivals, pairs, *, prediction_cache=None):
    """Score literal authoritative pairs; survival on all pairs is not ambiguity.

    An ambiguity requires agreement on every demonstration AND disagreement on
    the held-out query.  Evaluate all predictions even if an early demo refutes
    a rival, so errors cannot disappear through Boolean short-circuiting.
    """
    if len(pairs) < 2:
        raise ValueError("a lesson needs at least one demonstration and one query")
    for pair in pairs:
        grid_copy(pair["input"])
        grid_copy(pair["output"])
    cache = {} if prediction_cache is None else prediction_cache
    predictions = {name: [prediction(name, fn, pair["input"], cache) for pair in pairs]
                   for name, fn in sorted(rivals.items())}
    results = []
    for query_position, query in enumerate(pairs):
        train_positions = [i for i in range(len(pairs)) if i != query_position]
        row = {"query_position": query_position, "train_positions": train_positions,
               "rivals": {}, "ambiguities": [], "errors": [], "hook_findings": []}
        for name, values in predictions.items():
            failed_positions = [i for i, value in enumerate(values) if value["error"]]
            if failed_positions:
                row["rivals"][name] = "error"
                row["errors"].append({"rival": name, "pair_positions": failed_positions,
                                      "predictions": values})
                continue
            fits_demos = all(values[i]["output"] == pairs[i]["output"] for i in train_positions)
            agrees_query = values[query_position]["output"] == query["output"]
            status = "refuted" if not fits_demos else "survived_all" if agrees_query else "ambiguous"
            row["rivals"][name] = status
            if status == "ambiguous":
                row["ambiguities"].append({"rival": name,
                                           "predictions": [value["output"] for value in values]})
        hook = getattr(gen, "lesson_identifiable", None)
        if callable(hook):
            try:
                reasons = hook(deepcopy([pairs[i] for i in train_positions]), deepcopy(query))
                if not isinstance(reasons, (list, tuple)) or any(not isinstance(r, str) for r in reasons):
                    raise TypeError("lesson_identifiable must return list[str]")
                row["hook_findings"] = list(reasons)
            except Exception as exc:
                row["errors"].append({"hook": "lesson_identifiable",
                                      "error": f"{type(exc).__name__}: {exc}"})
        row["status"] = ("error" if row["errors"] else "ambiguous" if row["ambiguities"] else
                         "hook_rejected" if row["hook_findings"] else
                         "no_declared_ambiguity" if rivals else "no_contract")
        results.append(row)
    return results


def canonical_shortcut_fit(rivals, pairs):
    """Check all canonical variants/splits; retain every shortcut disagreement."""
    if not pairs:
        raise ValueError("canonical_pairs returned no labeled pairs")
    result, failures, cache = {}, [], {}
    for name, fn in sorted(rivals.items()):
        if not name.startswith("CANONICAL_SHORTCUTS:"):
            continue
        fitted, errors = 0, 0
        for index, pair in enumerate(pairs):
            value = prediction(name, fn, pair["input"], cache)
            fits = not value["error"] and value["output"] == pair["output"]
            fitted += int(fits)
            errors += int(bool(value["error"]))
            if not fits:
                failures.append({"kind": "canonical_shortcut_disagreement", "rival": name,
                                 "canonical_index": index, "pair": deepcopy(pair),
                                 "prediction": value})
        result[name] = {"pairs": len(pairs), "fits": fitted, "errors": errors,
                        "status": "error" if errors else "fits_all" if fitted == len(pairs) else "refuted"}
    return result, failures


def self_check_findings(gen, grid, band):
    checker = getattr(gen, "self_check", None)
    if checker is None:
        return []
    if not callable(checker):
        return ["self_check is not callable"]
    checked = deepcopy(grid)
    try:
        signature = inspect.signature(checker)
        accepts_band = "difficulty" in signature.parameters or any(
            p.kind == inspect.Parameter.VAR_KEYWORD for p in signature.parameters.values())
        findings = checker(checked, **({"difficulty": band} if accepts_band else {}))
        if findings is None:
            findings = []
        if not isinstance(findings, (list, tuple)) or any(not isinstance(x, str) for x in findings):
            raise TypeError("self_check must return list[str] or None")
        return list(findings) + (["self_check mutated its input"] if checked != grid else [])
    except Exception as exc:
        return [f"self_check: {type(exc).__name__}: {exc}"]


def window_validation(samples):
    """Keep raw duplicate/rejected positions; never replace or renumber them."""
    seen, duplicates, rejects = {}, [], []
    for position, sample in enumerate(samples):
        identity = {"pair_position": position, "sample_index": sample["sample_index"]}
        if sample["findings"]:
            rejects.append({**identity, "findings": list(sample["findings"])})
        value = sample.get("input_sha256")
        if value is not None:
            if value in seen:
                duplicates.append({**identity, "first_pair_position": seen[value],
                                   "first_sample_index": samples[seen[value]]["sample_index"],
                                   "input_sha256": value})
            else:
                seen[value] = position
    return rejects, duplicates


def report_status(report):
    if report["errors"] or report["summary"].get("rotation_errors", 0):
        return "error"
    if not report["rivals"]:
        return "no_contract"
    if report["summary"].get("ambiguous_rotations", 0):
        return "ambiguous"
    if report["failures"]:
        return "failed"
    if (not report.get("coverage_complete")
            or report["summary"].get("rotations_scored", 0) != report["sampler"]["expected_rotations"]):
        return "incomplete"
    return "no_declared_ambiguity"


def apply_labels(catalog, task_id, unique_inputs, expected, report, checkpoint):
    """Use only the public Catalog.apply API, with bounded, checked batches."""
    labels = {}
    items = list(unique_inputs.items())
    for start in range(0, len(items), APPLY_BATCH_SIZE):
        batch = items[start:start + APPLY_BATCH_SIZE]
        report["pending_apply"] = {"unique_input_offset": start,
                                   "inputs": [{"input_sha256": key, "input": grid} for key, grid in batch]}
        if checkpoint:
            checkpoint(report)
        receipt = catalog.apply(task_id, [grid for _, grid in batch], reference="canonical", timeout=120)
        report["pending_apply"]["receipt"] = receipt
        checks = {"task_id": task_id, "generator_sha256": expected["generator_sha256"],
                  "catalog_rule_hash": expected["rule_hash"], "executed_rule_hash": expected["rule_hash"],
                  "rule_task_id": expected["rule_task_id"], "rule_hash_matches_catalog": True}
        for name, value in checks.items():
            if receipt.get(name) != value:
                raise RuntimeError(f"apply receipt {name} changed: expected {value!r}, got {receipt.get(name)!r}")
        rule_text_hash = receipt.get("rule_text_sha256")
        if not isinstance(rule_text_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", rule_text_hash):
            raise RuntimeError("apply receipt lacks a valid rule_text_sha256")
        if report.get("rule_text_sha256", rule_text_hash) != rule_text_hash:
            raise RuntimeError("executed rule text changed between apply batches")
        report["executed_rule_hash"] = receipt["executed_rule_hash"]
        report["rule_text_sha256"] = rule_text_hash
        results = receipt.get("results", [])
        if len(results) != len(batch):
            raise RuntimeError("apply result count differs from requested input count")
        batch_row = {key: value for key, value in receipt.items() if key != "results"}
        batch_row.update({"unique_input_offset": start, "input_count": len(batch),
                          "input_sha256": [key for key, _ in batch]})
        report["apply_batches"].append(batch_row)
        for index, ((key, grid), result) in enumerate(zip(batch, results, strict=True)):
            if result.get("index") != index or result.get("input") != grid or result.get("input_sha256") != key:
                raise RuntimeError(f"apply input identity/order mismatch at unique input {start + index}")
            output = result.get("output")
            error = result.get("error")
            if result.get("valid_output") is not True or error:
                labels[key] = {"output": output, "error": error or "apply marked output invalid"}
                report.setdefault("authority_failures", []).append({
                    "unique_input_index": start + index, "input_sha256": key,
                    "input": deepcopy(grid), "result": deepcopy(result)})
            else:
                output = grid_copy(output)
                if result.get("output_sha256") != digest(output):
                    raise RuntimeError(f"apply output hash mismatch at unique input {start + index}")
                labels[key] = {"output": output, "error": None}
        report.pop("pending_apply")
        report["summary"].update({"unique_inputs_processed": len(labels),
                                  "unique_inputs_labeled": sum(not result["error"] for result in labels.values()),
                                  "unique_label_errors": sum(bool(result["error"]) for result in labels.values())})
        if checkpoint:
            checkpoint(report)
    return labels


def run_probe(*, task=DEFAULT_TASK, seed_start=910000, seeds=16, period=3, train=5,
              bands=("easy", "medium", "hard"), root=None, checkpoint=None):
    for name, value in (("seeds", seeds), ("period", period), ("train", train)):
        if type(value) is not int or value < 1:
            raise ValueError(f"{name} must be a positive integer")
    if type(seed_start) is not int:
        raise ValueError("seed_start must be an integer")
    if not bands or len(set(bands)) != len(bands) or any(b not in (None, "easy", "medium", "hard") for b in bands):
        raise ValueError("bands must be distinct easy,medium,hard,default values")
    root = Path(root).resolve() if root is not None else find_tree(__file__)
    expected_windows = len(bands) * seeds * period
    report = {"schema": "arcpuzzles-cyclic-lesson-windows-v1", "task_id": task,
              "root": str(root), "status": "incomplete", "passed": False,
              "tool_sha256": file_digest(__file__), "errors": [], "failures": [],
              "rivals": [], "windows": [], "per_band": {}, "apply_batches": [], "summary": {},
              "sample_failures": [], "direct_streams": [],
              "sampler": {"mode": "direct_consecutive_indices", "seed_start": seed_start,
                          "seeds": seeds, "seed_values": list(range(seed_start, seed_start + seeds)),
                          "period": period, "train": train, "test": 1,
                          "bands": [b or "default" for b in bands], "overrides": {},
                          "start_indices": list(range(period)),
                          "sample_indices_per_seed_band": list(range(period + train)),
                          "query_positions": list(range(train + 1)),
                          "expected_windows": expected_windows,
                          "expected_rotations": expected_windows * (train + 1),
                          "rotation_recipe": "hold out each pair once; preserve remaining order"},
              "limits": ["Finite declared-rival evidence, not universal identifiability or approval.",
                         "Direct generate(seed, sample_index, difficulty=band) calls; no rejection replacement.",
                         "Raw starts never become claimed production-accepted starts. Use shared lesson-census for production.",
                         "Only default axis choices are probed; explicit axis overrides have no curriculum guarantee here.",
                         "Unique-input counts use exact integer-grid hashes, not semantic equivalence.",
                         "Rival predictions are cached by namespaced name/input hash and require pure deterministic rivals.",
                         "Successful windows retain indices and hashes; every failing window retains its available grids and labels."]}
    try:
        catalog, support = local_environment(root)
        row = catalog.describe(task)
        task = row["id"]
        report["task_id"] = task
        if row["kind"] != "per_puzzle":
            raise ValueError("this direct-window probe requires a per-puzzle generator")
        source = select_generator(root, task, row)
        initial_hash = file_digest(source)
        if initial_hash != row["generator_sha256"]:
            raise RuntimeError("selected generator differs from Catalog's source")
        gen = load_source(source, "lesson_window_generator")
        report.update({"generator_path": str(source.relative_to(root)),
                       "generator_sha256": initial_hash, "generator_version": getattr(gen, "VERSION", None),
                       "declared_rule_hash": getattr(gen, "RULE_HASH", None),
                       "catalog_rule_hash": row["rule_hash"], "rule_task_id": row.get("rule_task_id", task),
                       "reviewer_support_sha256": file_digest(support.__file__)})
        if file_digest(source) != initial_hash:
            raise RuntimeError("generator changed during explicit source import")
        rivals, declarations, errors = declared_rivals(gen)
        report.update({"rivals": sorted(rivals), "declarations": declarations,
                       "lesson_hook_present": callable(getattr(gen, "lesson_identifiable", None)),
                       "self_check_present": callable(getattr(gen, "self_check", None))})
        report["errors"].extend(errors)
        if not rivals:
            report["contract_note"] = "No named rival contract; no identifiability pass is possible."
            report["status"] = report_status(report)
            return report
        canonical = support.canonical_pairs(report["rule_task_id"], root=root)
        report["canonical_pairs"] = len(canonical)
        report["canonical_pairs_sha256"] = digest(canonical)
        report["canonical_shortcut_fit"], failures = canonical_shortcut_fit(rivals, canonical)
        report["failures"].extend(failures)
        for failure in failures:
            if failure["prediction"]["error"]:
                report["errors"].append(failure["prediction"]["error"])
        if report["declared_rule_hash"] is not None and report["declared_rule_hash"] != row["rule_hash"]:
            report["errors"].append("declared RULE_HASH differs from current catalog rule hash")
        streams, unique_inputs, generated_hashes = [], {}, set()
        for pair in canonical:
            unique_inputs.setdefault(digest(pair["input"]), pair["input"])
        for band in bands:
            band_name = band or "default"
            for seed in range(seed_start, seed_start + seeds):
                samples = []
                for sample_index in range(period + train):
                    sample = {"sample_index": sample_index, "input": None, "input_sha256": None,
                              "output": None, "output_sha256": None, "findings": []}
                    try:
                        raw = gen.generate(seed=seed, sample_index=sample_index, difficulty=band)
                        raw_grid = raw.get("input") if isinstance(raw, dict) else raw
                        sample["input"] = evidence_value(raw_grid)
                        grid = grid_copy(raw_grid)
                        key = digest(grid)
                        sample.update({"input": grid, "input_sha256": key})
                        sample["findings"].extend(self_check_findings(gen, grid, band))
                        unique_inputs.setdefault(key, grid)
                        generated_hashes.add(key)
                    except Exception as exc:
                        sample["findings"].append(f"generate/input: {type(exc).__name__}: {exc}")
                    samples.append(sample)
                    if sample["findings"]:
                        report["sample_failures"].append({"band": band_name, "seed": seed, **deepcopy(sample)})
                streams.append((band_name, seed, samples))
                report["direct_streams"].append({"band": band_name, "seed": seed,
                                                  "sample_indices": [s["sample_index"] for s in samples],
                                                  "input_sha256": [s["input_sha256"] for s in samples]})
        report["summary"].update({"generated_draws": len(streams) * (period + train),
                                   "unique_inputs": len(generated_hashes),
                                   "unique_generated_inputs": len(generated_hashes),
                                   "unique_authority_inputs": len(unique_inputs)})
        if file_digest(source) != initial_hash:
            raise RuntimeError("generator changed during direct generation")
        if checkpoint:
            checkpoint(report)
        expected = {**row, "rule_task_id": report["rule_task_id"]}
        labels = apply_labels(catalog, task, unique_inputs, expected, report, checkpoint)
        for index, pair in enumerate(canonical):
            label = labels[digest(pair["input"])]
            if label["error"] or label["output"] != pair["output"]:
                report["failures"].append({"kind": "canonical_authority_disagreement", "canonical_index": index,
                                           "pair": pair, "racket_result": label})
                report["errors"].append(f"canonical pair {index}: Racket did not reproduce the ledger label")
        totals, cache = Counter(), {}
        for band_name, seed, samples in streams:
            for sample in samples:
                if sample["input_sha256"] is None:
                    continue
                label = labels[sample["input_sha256"]]
                if label["error"]:
                    sample["findings"].append(f"Racket: {label['error']}")
                    report["errors"].append(f"{band_name} seed {seed} sample {sample['sample_index']}: {label['error']}")
                    continue
                sample["output"] = label["output"]
                sample["output_sha256"] = digest(label["output"])
                if not getattr(gen, "ALLOW_IDENTITY_OUTPUT", False) and sample["input"] == sample["output"]:
                    sample["findings"].append("validate.output_equals_input")
            band_row = report["per_band"].setdefault(band_name, {
                "start_counts": {str(i): 0 for i in range(period)},
                "scored_query_positions_by_start": {str(i): [0] * (train + 1) for i in range(period)},
                "rival_rotation_counts": {name: {} for name in sorted(rivals)}})
            totals["validation_rejected_draws"] += sum(bool(s["findings"]) for s in samples)
            for start in range(period):
                selected = samples[start:start + train + 1]
                rejects, duplicates = window_validation(selected)
                identity = {"band": band_name, "seed": seed, "start": start,
                            "sample_indices": [s["sample_index"] for s in selected]}
                window = {**identity, "input_sha256": [s["input_sha256"] for s in selected],
                          "output_sha256": [s["output_sha256"] for s in selected],
                          "validation_rejects": rejects, "duplicate_inputs": duplicates}
                band_row["start_counts"][str(start)] += 1
                totals["windows_requested"] += 1
                totals["windows_with_duplicates"] += int(bool(duplicates))
                pairs = [{"input": s["input"], "output": s["output"]} for s in selected]
                complete = all(s["output_sha256"] is not None for s in selected)
                rotations = score_rotations(gen, rivals, pairs, prediction_cache=cache) if complete else []
                window["rotation_statuses"] = [r["status"] for r in rotations] if complete else ["blocked"] * (train + 1)
                window["status"] = ("blocked" if not complete else "validation_rejected" if rejects or duplicates else
                                     "failed" if any(r["status"] != "no_declared_ambiguity" for r in rotations) else
                                     "no_declared_ambiguity")
                totals["windows_labeled"] += int(complete)
                totals["windows_valid_direct"] += int(complete and not rejects and not duplicates)
                totals["windows_blocked"] += int(not complete)
                totals["rotations_scored"] += len(rotations)
                for rotation in rotations:
                    query_position = rotation["query_position"]
                    band_row["scored_query_positions_by_start"][str(start)][query_position] += 1
                    totals["ambiguous_rotations"] += int(bool(rotation["ambiguities"]))
                    totals["rotation_errors"] += int(bool(rotation["errors"]))
                    totals["hook_rejected_rotations"] += int(bool(rotation["hook_findings"]))
                    for name, status in rotation["rivals"].items():
                        counts = band_row["rival_rotation_counts"][name]
                        counts[status] = counts.get(status, 0) + 1
                if window["status"] != "no_declared_ambiguity":
                    report["failures"].append({"kind": "direct_window_failure", **identity,
                                               "samples": deepcopy(selected), "validation_rejects": rejects,
                                               "duplicate_inputs": duplicates,
                                               "rotations": [r for r in rotations if r["status"] != "no_declared_ambiguity"]})
                report["windows"].append(window)
            report["summary"].update(totals)
            if checkpoint:
                checkpoint(report)
        if file_digest(source) != initial_hash or catalog.describe(task)["rule_hash"] != row["rule_hash"]:
            raise RuntimeError("generator or canonical rule changed during the probe")
        report["coverage_complete"] = (
            totals["windows_requested"] == expected_windows
            and totals["rotations_scored"] == report["sampler"]["expected_rotations"]
            and all(all(value == seeds for value in band["start_counts"].values())
                    and all(all(value == seeds for value in counts)
                            for counts in band["scored_query_positions_by_start"].values())
                    for band in report["per_band"].values()))
    except Exception as exc:
        report["errors"].append(f"{type(exc).__name__}: {exc}")
        if hasattr(exc, "run"):
            report["failed_execution"] = exc.run
    report["status"] = report_status(report)
    report["passed"] = report["status"] == "no_declared_ambiguity" and report.get("coverage_complete", False)
    return report


def parse_bands(text):
    values = []
    for word in text.split(","):
        value = word.strip().lower()
        if value in ("default", "none", "null"):
            values.append(None)
        elif value in ("easy", "medium", "hard"):
            values.append(value)
        else:
            raise argparse.ArgumentTypeError(f"unknown band: {word!r}")
    if len(set(values)) != len(values):
        raise argparse.ArgumentTypeError("bands must be distinct")
    return tuple(values)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--task", default=DEFAULT_TASK)
    parser.add_argument("--seed-start", type=int, default=910000)
    parser.add_argument("--seeds", type=int, default=16)
    parser.add_argument("--period", type=int, default=3, help="enumerate every start in 0..period-1")
    parser.add_argument("--train", type=int, default=5, help="demonstrations per rotated one-query lesson")
    parser.add_argument("--bands", type=parse_bands, default=("easy", "medium", "hard"),
                        help="comma-separated easy,medium,hard,default (default: easy,medium,hard)")
    parser.add_argument("--library", type=Path, help="explicit self-contained library; otherwise bind to this tool's tree")
    parser.add_argument("--out", type=Path, required=True, help="new JSON evidence path")
    args = parser.parse_args(argv)
    if min(args.seeds, args.period, args.train) < 1:
        parser.error("--seeds, --period, and --train must be positive")
    if args.out.exists():
        parser.error("--out already exists; preserve prior evidence and choose a new path")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    def checkpoint(report):
        temporary = args.out.with_name(args.out.name + ".tmp")
        temporary.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        temporary.replace(args.out)
    report = run_probe(task=args.task, seed_start=args.seed_start, seeds=args.seeds,
                       period=args.period, train=args.train, bands=args.bands, root=args.library,
                       checkpoint=checkpoint)
    checkpoint(report)
    print(json.dumps({"task_id": report["task_id"], "status": report["status"], "passed": report["passed"],
                      "summary": report["summary"], "failure_records": len(report["failures"]),
                      "errors": report["errors"], "out": str(args.out)}, indent=2))
    return 0 if report["passed"] else 2 if report["status"] in ("error", "no_contract", "incomplete") else 1


if __name__ == "__main__":
    raise SystemExit(main())
