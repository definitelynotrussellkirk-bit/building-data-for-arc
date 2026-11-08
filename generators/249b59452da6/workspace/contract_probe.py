#!/usr/bin/env python3
"""Replayable, independent contract and teaching-coverage probe for E82.

Run from a library checkout, for example::

    python3 ../run_with_racket.py python3 \
      generators/249b59452da6/workspace/contract_probe.py \
      --out ../checks/contract-final --per-band 100 --require-teaching-support

``--joint`` adds every 4..18 x 4..18 x 1..10 x 2..5 exact-axis
combination at the requested seed, sample index 0, default difficulty: 9,000
requests. Individual axis values are always checked in all four bands.
Structured joint rejections are reported as unsupported combinations; this
probe does not assert that every such combination is mathematically impossible.

The Python oracle is an independent diagnostic implementation, not the rule
authority. ``--racket`` additionally checks canonical pairs, deterministic
motifs, and representative default inputs with public ``Catalog.apply``.
``--exhaustive-racket`` adds all 729 2x3 inputs over {0, 2, 7}. These optional
flags require the library Catalog layout and fail explicitly if unavailable.
The remaining checks also work in a staged runtime using reviewer_support.

Every case and full failure is retained in compressed JSONL. The destination
must be new; existing evidence is never overwritten. No generator helpers are
used to identify active windows, count colors, or compute diagnostic outputs.
"""
from __future__ import annotations

import argparse
import copy
from collections import Counter
from datetime import datetime, timezone
import gzip
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys
import time
import traceback
from typing import Any


TASK_ID = "249b59452da6"
BANDS = (None, "easy", "medium", "hard")
LIMITS = {"grid_h": (4, 18), "grid_w": (4, 18),
          "n_pairs": (1, 10), "palette_size": (2, 5)}
NAMESPACES = ("SEMANTIC_RIVALS", "CANONICAL_SHORTCUTS", "LESSON_COMPETITORS")


def bootstrap_support() -> None:
    """Find the public support module without assuming a fixed tree depth."""
    for parent in Path(__file__).resolve().parents:
        for candidate in (parent / "shared" / "runtime", parent):
            if (candidate / "reviewer_support.py").is_file():
                sys.path.insert(0, str(candidate))
                return
    raise ImportError("Cannot locate public reviewer_support relative to this probe")


bootstrap_support()
from reviewer_support import canonical_pairs, canonical_path, find_root  # noqa: E402


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def file_digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def source_snapshot(paths: dict[str, Path]) -> dict[str, dict[str, Any]]:
    """Exact source identities; callers compare snapshots before and after work."""
    return {name: {"path": str(path.resolve()), "bytes": path.stat().st_size,
                   "sha256": file_digest(path)} for name, path in sorted(paths.items())}


def compressed_artifact_metadata(path: Path) -> dict[str, Any]:
    """Hash both representations by streaming; do not materialize a large report."""
    restored_hash = hashlib.sha256()
    restored_bytes = 0
    records = 0
    with gzip.open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            restored_hash.update(chunk)
            restored_bytes += len(chunk)
            records += chunk.count(b"\n")
    restored_name = path.name.removesuffix(".gz")
    return {"filename": path.name, "compressed_bytes": path.stat().st_size,
            "compressed_sha256": file_digest(path), "uncompressed_bytes": restored_bytes,
            "uncompressed_sha256": restored_hash.hexdigest(), "jsonl_records": records,
            "restored_filename": restored_name,
            "restore_command": f"gzip -dc {path.name} > {restored_name}"}


def band_name(band: str | None) -> str:
    return "default" if band is None else band


def grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list"]
    if any(not isinstance(row, list) or not row for row in grid):
        return ["rows must be nonempty lists"]
    if len({len(row) for row in grid}) != 1:
        return ["grid is ragged"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["colors must be exact integers in 0..9"]
    return []


def eligible_windows(grid: list[list[int]]) -> set[tuple[int, int]]:
    """Derive anchors from neighboring red coordinates, independently of gen."""
    red = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
           if value == 2}
    anchors = set()
    for r, c in red:
        for dc in (-1, 1):
            if ((r + 1, c + dc) in red and grid[r][c + dc] == 0
                    and grid[r + 1][c] == 0):
                anchors.add((r, min(c, c + dc)))
    return anchors


def independent_oracle(grid: list[list[int]]) -> list[list[int]]:
    """Diagnostic oracle; authoritative parity is a separate optional check."""
    result = copy.deepcopy(grid)
    for r, c in eligible_windows(grid):
        for rr, cc in ((r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1)):
            if grid[rr][cc] == 0:
                result[rr][cc] = 3
    return result


def independently_observe(grid: list[list[int]]) -> dict[str, int]:
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "n_pairs": len(eligible_windows(grid)),
            "palette_size": len({v for row in grid for v in row})}


def observation_errors(grid: Any, requested: dict[str, Any], observed: Any) -> list[str]:
    """Pure assessment used by the CLI and focused regression tests."""
    errors = grid_errors(grid)
    if errors:
        return errors
    actual = independently_observe(grid)
    for name, value in requested.items():
        if name in actual and actual[name] != value:
            errors.append(f"requested {name}={value!r}; independent count is {actual[name]}")
    if not isinstance(observed, dict):
        errors.append("observe_overrides must return a dict")
        return errors
    for name, actual_value in actual.items():
        value = observed.get(name)
        if type(value) is not int:
            errors.append(f"observer {name} must be an exact integer")
        elif value != actual_value:
            errors.append(f"observer {name}={value}; independent count is {actual_value}")
    return errors


def input_contract_errors(grid: Any) -> list[str]:
    errors = grid_errors(grid)
    if errors:
        return errors
    observed = independently_observe(grid)
    for name, (lo, hi) in LIMITS.items():
        if not lo <= observed[name] <= hi:
            errors.append(f"{name}={observed[name]} outside {lo}..{hi}")
    flat = [v for row in grid for v in row]
    if 0 not in flat or 2 not in flat:
        errors.append("both background 0 and trigger color 2 must be present")
    if flat.count(0) * 2 < len(flat):
        errors.append("fewer than half of the input cells are background zero")
    return errors


class Evidence:
    def __init__(self, output: Path):
        output.mkdir(parents=True, exist_ok=False)
        self.output = output
        self.cases_file = gzip.open(output / "cases.jsonl.gz", "wt", encoding="utf-8")
        self.failures_file = gzip.open(output / "failures.jsonl.gz", "wt", encoding="utf-8")
        self.case_count = 0
        self.failure_count = 0
        self.error_counts: Counter[str] = Counter()
        self.failure_examples: list[dict[str, Any]] = []
        self.finalization_failures: list[dict[str, Any]] = []
        self.warnings: list[dict[str, Any]] = []
        self.report: dict[str, Any] = {}

    def case(self, value: dict[str, Any]) -> dict[str, Any]:
        self.case_count += 1
        value = {"case_id": self.case_count, **value}
        self.cases_file.write(json.dumps(value, sort_keys=True, allow_nan=False) + "\n")
        return value

    def error(self, code: str, **details: Any) -> None:
        self.failure_count += 1
        self.error_counts[code] += 1
        row = {"failure_id": self.failure_count, "code": code, **details}
        encoded = json.dumps(row, sort_keys=True, default=repr) + "\n"
        if self.failures_file.closed:
            # Closed evidence must remain byte-for-byte unchanged while its
            # integrity is checked. The final JSON report retains these rows.
            self.finalization_failures.append(row)
        else:
            self.failures_file.write(encoded)
        if len(self.failure_examples) < 30:
            self.failure_examples.append({k: v for k, v in row.items()
                                          if k not in {"input", "output", "expected", "grids", "pairs"}})

    def warn(self, code: str, **details: Any) -> None:
        self.warnings.append({"code": code, **details})

    def close(self) -> None:
        self.cases_file.close()
        self.failures_file.close()


def checked_hook(evidence: Evidence, function: Any, grid: Any, *, name: str,
                 case: dict[str, Any], kwargs: dict[str, Any] | None = None) -> tuple[bool, Any]:
    replay = {key: case[key] for key in ("seed", "sample_index", "difficulty", "requested",
                                        "variant", "split", "pair_index") if key in case}
    if not callable(function):
        evidence.error("missing_hook", hook=name, case_id=case.get("case_id"), input=grid, **replay)
        return False, None
    supplied = copy.deepcopy(grid)
    before = copy.deepcopy(supplied)
    try:
        result = function(supplied, **(kwargs or {}))
    except Exception as exc:
        evidence.error("hook_exception", hook=name, case_id=case.get("case_id"), input=grid,
                       exception=type(exc).__name__, message=str(exc), traceback=traceback.format_exc(), **replay)
        return False, None
    if supplied != before:
        evidence.error("hook_mutated_input", hook=name, case_id=case.get("case_id"),
                       input=before, output=supplied, **replay)
        return False, result
    return True, result


def check_materialized(module: Any, evidence: Evidence, grid: Any, *, scope: str,
                       seed: int, index: int, band: str | None,
                       requested: dict[str, Any] | None = None,
                       determinism: str = "not_requested") -> dict[str, Any] | None:
    requested = requested or {}
    case = {"scope": scope, "seed": seed, "sample_index": index,
            "difficulty": band, "requested": requested, "input": grid,
            "deterministic_replay": determinism}
    errors = input_contract_errors(grid)
    if errors:
        case = evidence.case({**case, "status": "invalid_input", "errors": errors})
        evidence.error("input_contract", **case)
        return None
    observed = independently_observe(grid)
    expected = independent_oracle(grid)
    case.update({"independent_observed": observed, "input_sha256": digest(grid),
                 "independent_oracle_output": expected,
                 "eligible_anchors": sorted(eligible_windows(grid)),
                 "zero_cells": sum(row.count(0) for row in grid)})
    ok, declared = checked_hook(evidence, getattr(module, "observe_overrides", None), grid,
                                name="observe_overrides", case=case)
    case["declared_observed"] = declared
    if ok:
        observed_errors = observation_errors(grid, requested, declared)
        if observed_errors:
            evidence.error("override_observation", **case, errors=observed_errors)
    for key, value in requested.items():
        if key in observed and observed[key] != value:
            evidence.error("requested_axis_mismatch", **case, axis=key,
                           requested_value=value, actual_value=observed[key])
    ok, validation = checked_hook(evidence, getattr(module, "self_check", None), grid,
                                  name="self_check", case=case, kwargs={"difficulty": band})
    case["self_check"] = validation
    if ok and (not isinstance(validation, list) or validation
               or any(not isinstance(item, str) for item in validation)):
        evidence.error("generated_selfcheck_rejected", **case)
    strict = getattr(module, "strict_canonical_like", None)
    if callable(strict):
        ok, value = checked_hook(evidence, strict, grid, name="strict_canonical_like", case=case)
        if ok:
            if type(value) is bool:
                case["strict_canonical_like"] = value
            elif isinstance(value, list) and all(isinstance(item, str) for item in value):
                case["strict_canonical_like"] = not value
                case["strict_reasons"] = value
            else:
                evidence.error("strict_hook_contract", **case, result=repr(value))
    return evidence.case({**case, "status": "materialized"})


def generate_case(module: Any, evidence: Evidence, *, scope: str, seed: int, index: int,
                  band: str | None, requested: dict[str, Any] | None = None,
                  allow_joint_rejection: bool = False, repeat: bool = False) -> dict[str, Any] | None:
    requested = requested or {}
    context = {"scope": scope, "seed": seed, "sample_index": index,
               "difficulty": band, "requested": requested}
    try:
        grid = module.generate(seed, index, difficulty=band, **requested)
    except Exception as exc:
        axes = getattr(exc, "incompatible_axes", None)
        structured = (isinstance(exc, ValueError) and isinstance(axes, (tuple, list))
                      and bool(axes) and all(isinstance(name, str) and name in LIMITS for name in axes)
                      and set(requested).issubset(set(axes)))
        record = evidence.case({**context, "status": "rejected", "exception": type(exc).__name__,
                                "message": str(exc), "incompatible_axes": axes,
                                "structured_joint_rejection": structured})
        if not (allow_joint_rejection and structured):
            evidence.error("generation_exception", **record, traceback=traceback.format_exc())
        return record
    determinism = "not_requested"
    if repeat:
        try:
            second = module.generate(seed, index, difficulty=band, **requested)
        except Exception as exc:
            determinism = "raised"
            evidence.error("determinism_repeat_exception", **context, input=grid,
                           exception=type(exc).__name__, message=str(exc))
        else:
            if second != grid:
                determinism = "different"
                evidence.error("nondeterministic_generation", **context, input=grid, output=second)
            else:
                determinism = "matched"
    return check_materialized(module, evidence, grid, scope=scope, seed=seed, index=index,
                              band=band, requested=requested, determinism=determinism)


def rule_registries(module: Any, evidence: Evidence) -> dict[str, Any]:
    rules = {}
    for namespace in NAMESPACES:
        declared = getattr(module, namespace, None)
        if not isinstance(declared, dict) or not declared:
            evidence.error("missing_rule_registry", namespace=namespace)
            continue
        for name, function in declared.items():
            if not isinstance(name, str) or not callable(function):
                evidence.error("invalid_rule_registry", namespace=namespace, name=repr(name))
            else:
                rules[f"{namespace}.{name}"] = function
    return rules


def predict_rules(evidence: Evidence, rules: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    predictions = {}
    for name, function in rules.items():
        ok, output = checked_hook(evidence, function, case["input"], name=name, case=case)
        if not ok:
            continue
        errors = grid_errors(output)
        if not errors and (len(output), len(output[0])) != (len(case["input"]), len(case["input"][0])):
            errors = ["rival changed grid dimensions"]
        if errors:
            evidence.error("rival_output_contract", hook=name, case_id=case.get("case_id"),
                           input=case["input"], output=output, errors=errors)
        else:
            predictions[name] = output
    return predictions


def check_canonical(module: Any, evidence: Evidence, rules: dict[str, Any], root: Path) -> list[dict[str, Any]]:
    pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    stats = {"pairs": len(pairs), "independent_oracle_matches": 0,
             "shortcut_matches": Counter(), "identities": []}
    for pair in pairs:
        identity = {key: pair[key] for key in ("variant", "split", "pair_index")}
        stats["identities"].append(identity)
        case = evidence.case({"scope": "canonical", **identity, "input": pair["input"],
                              "stored_output": pair["output"], "input_sha256": digest(pair["input"])})
        expected = independent_oracle(pair["input"])
        if expected == pair["output"]:
            stats["independent_oracle_matches"] += 1
        else:
            evidence.error("oracle_canonical_disagreement", **case, expected=expected)
        for hook_name in ("self_check", "strict_canonical_like"):
            ok, result = checked_hook(evidence, getattr(module, hook_name, None), pair["input"],
                                      name=hook_name, case=case)
            accepted = (result is True if type(result) is bool else
                        isinstance(result, list) and not result)
            if ok and not accepted:
                evidence.error("canonical_hook_rejected", **case, hook=hook_name, result=result)
        for name, prediction in predict_rules(evidence, rules, case).items():
            if not name.startswith("CANONICAL_SHORTCUTS."):
                continue
            if prediction == pair["output"]:
                stats["shortcut_matches"][name] += 1
            else:
                evidence.error("claimed_shortcut_does_not_fit_canonical", **case,
                               rival=name, output=prediction)
    evidence.report["canonical"] = stats
    return pairs


def score_lesson_rotations(cases: list[dict[str, Any]], *, names: list[str],
                           shortcuts: list[str], n_train: int,
                           require_teaching_support: bool) -> dict[str, Any]:
    """Score actual consecutive inputs; return full ambiguous/unsupported lessons."""
    stats: dict[str, Any] = {"consecutive_windows": 0, "rotations": 0,
                            "survived_demos": Counter(), "survived_all": Counter(),
                            "ambiguities": [], "insufficient_teaching_support": [],
                            "teaching_support": {name: {"minimum_distinct_refuting_demos": None,
                                                       "histogram": Counter()} for name in shortcuts}}
    width = n_train + 1
    for offset in range(max(0, len(cases) - width + 1)):
        block = cases[offset:offset + width]
        if any(block[j]["sample_index"] != block[0]["sample_index"] + j for j in range(width)):
            continue
        stats["consecutive_windows"] += 1
        for query in range(width):
            stats["rotations"] += 1
            for name in names:
                if any(name not in case.get("predictions", {}) for case in block):
                    continue  # The failed hook already creates a hard probe error.
                matches = [case["predictions"][name] == case["independent_oracle_output"] for case in block]
                survived_demos = all(matches[j] for j in range(width) if j != query)
                survived_all = all(matches)
                stats["survived_demos"][name] += int(survived_demos)
                stats["survived_all"][name] += int(survived_all)
                detail = {"rival": name, "start_index": block[0]["sample_index"],
                          "seed": block[0]["seed"], "difficulty": block[0]["difficulty"],
                          "query_rotation": query, "case_ids": [case["case_id"] for case in block],
                          "grids": [case["input"] for case in block],
                          "expected": [case["independent_oracle_output"] for case in block],
                          "output": [case["predictions"][name] for case in block]}
                if survived_demos and not matches[query]:
                    stats["ambiguities"].append(detail)
                if name in stats["teaching_support"]:
                    refuting = {block[j]["input_sha256"] for j in range(width)
                                if j != query and not matches[j]}
                    count = len(refuting)
                    support = stats["teaching_support"][name]
                    current = support["minimum_distinct_refuting_demos"]
                    support["minimum_distinct_refuting_demos"] = count if current is None else min(current, count)
                    support["histogram"][str(count)] += 1
                    if require_teaching_support and count < 2:
                        stats["insufficient_teaching_support"].append({**detail, "distinct_refuting_demos": count})
    return stats


def check_defaults(module: Any, evidence: Evidence, rules: dict[str, Any], *, seed: int,
                   per_band: int, require_teaching_support: bool) -> list[dict[str, Any]]:
    witnesses = getattr(module, "SEMANTIC_WITNESSES", {})
    claims = getattr(module, "WITNESS_RIVALS", {})
    if not isinstance(witnesses, dict) or not witnesses:
        evidence.error("missing_witness_registry")
        witnesses = {}
    if not isinstance(claims, dict):
        evidence.error("invalid_witness_rivals_registry")
        claims = {}
    for name, function in witnesses.items():
        if not isinstance(name, str) or not callable(function):
            evidence.error("invalid_witness", name=repr(name))
    witnesses = {name: fn for name, fn in witnesses.items() if isinstance(name, str) and callable(fn)}
    for name, nominated in claims.items():
        if name not in witnesses or not isinstance(nominated, (tuple, list)) or not nominated:
            evidence.error("invalid_witness_claim", witness=name, rivals=nominated)
            continue
        for rival in nominated:
            if f"SEMANTIC_RIVALS.{rival}" not in rules:
                evidence.error("unknown_witness_rival", witness=name, rival=rival)
    n_train = getattr(module, "EXAMPLES_NEEDED", 3)
    if type(n_train) is not int or n_train < 1:
        evidence.error("invalid_examples_needed", value=repr(n_train))
        n_train = 3
    representatives = []
    defaults = {}
    for band in BANDS:
        records = []
        counts = {"attempted": per_band, "materialized": 0, "deterministic_replays_matched": 0,
                  "strict_accepted": 0, "duplicate_input_hashes": [],
                  "witness_hits": Counter(), "rival_refutations": Counter(),
                  "observed_histograms": {key: Counter() for key in LIMITS}}
        seen: dict[str, int] = {}
        for index in range(per_band):
            case = generate_case(module, evidence, scope="defaults", seed=seed, index=index,
                                 band=band, repeat=True)
            if not case or case.get("status") != "materialized":
                continue
            counts["materialized"] += 1
            counts["deterministic_replays_matched"] += int(case["deterministic_replay"] == "matched")
            counts["strict_accepted"] += int(case.get("strict_canonical_like", False))
            for key, value in case["independent_observed"].items():
                counts["observed_histograms"][key][str(value)] += 1
            if case["input_sha256"] in seen:
                counts["duplicate_input_hashes"].append({"first_index": seen[case["input_sha256"]],
                                                         "second_index": index,
                                                         "input_sha256": case["input_sha256"]})
            else:
                seen[case["input_sha256"]] = index
            case["predictions"] = predict_rules(evidence, rules, case)
            for name, prediction in case["predictions"].items():
                counts["rival_refutations"][name] += int(prediction != case["independent_oracle_output"])
            for name, function in witnesses.items():
                ok, fired = checked_hook(evidence, function, case["input"], name=f"witness.{name}", case=case)
                if not ok:
                    continue
                if type(fired) is not bool:
                    evidence.error("witness_return_contract", witness=name, case_id=case["case_id"],
                                   input=case["input"], result=repr(fired))
                    continue
                counts["witness_hits"][name] += int(fired)
                nominated = claims.get(name, ())
                if fired and isinstance(nominated, (tuple, list)) and nominated:
                    disagrees = any(case["predictions"].get(f"SEMANTIC_RIVALS.{rival}")
                                    != case["independent_oracle_output"]
                                    for rival in nominated
                                    if f"SEMANTIC_RIVALS.{rival}" in case["predictions"])
                    if not disagrees:
                        evidence.error("witness_failed_to_refute_claimed_rival", witness=name,
                                       rivals=nominated, case_id=case["case_id"], input=case["input"],
                                       expected=case["independent_oracle_output"],
                                       predictions=case["predictions"])
            evidence.case({"scope": "default_semantics", "source_case_id": case["case_id"],
                           "seed": seed, "sample_index": index, "difficulty": band,
                           "input": case["input"], "predictions": case["predictions"]})
            records.append(case)
            if len(records) <= 4:
                representatives.append(case)
        lesson_stats = score_lesson_rotations(
            records, names=sorted(rules), shortcuts=[n for n in rules if n.startswith("CANONICAL_SHORTCUTS.")],
            n_train=n_train, require_teaching_support=require_teaching_support)
        for failure in lesson_stats.pop("ambiguities"):
            evidence.error("lesson_query_ambiguity", **failure)
        for failure in lesson_stats.pop("insufficient_teaching_support"):
            evidence.error("teaching_support_below_requested_floor", **failure)
        if not lesson_stats["rotations"]:
            evidence.error("no_lesson_rotations_checked", band=band_name(band), materialized=len(records), n_train=n_train)
        counts["lessons"] = lesson_stats
        counts["distinct_inputs"] = len(seen)
        defaults[band_name(band)] = counts
        print(f"contract_probe: {band_name(band)} defaults {len(records)}/{per_band}, "
              f"{lesson_stats['rotations']} lesson rotations", file=sys.stderr, flush=True)
    for name in witnesses:
        hits = sum(value["witness_hits"][name] for value in defaults.values())
        if not hits:
            evidence.warn("declared_witness_not_observed", witness=name, sampled=4 * per_band)
    for name in rules:
        hits = sum(value["rival_refutations"][name] for value in defaults.values())
        if not hits:
            evidence.warn("teaching_gap_no_default_refutation", rival=name, sampled=4 * per_band)
    evidence.report["defaults"] = defaults
    evidence.report["lesson_contract"] = {
        "n_train": n_train, "query_rotations_per_consecutive_window": n_train + 1,
        "labels": "independent Python diagnostic oracle; Racket parity only when requested",
        "teaching_support_floor": 2 if require_teaching_support else None,
        "teaching_support_distinctness": "input SHA-256 among the demonstrations",
        "teaching_coverage_is_separate_from_label_correctness": True,
    }
    return representatives


def check_override_axes(module: Any, evidence: Evidence, *, seed: int, joint: bool) -> None:
    axes = getattr(module, "AXES", {})
    if not isinstance(axes, dict) or set(axes) != set(LIMITS):
        evidence.error("axis_declaration_mismatch", expected=sorted(LIMITS), actual=repr(axes))
    stats = {"single_axis_attempts": 0, "invalid_override_attempts": 0,
             "invalid_overrides_rejected": 0, "joint_attempts": 0,
             "joint_materialized": 0, "joint_structured_rejections": 0,
             "joint_scope": "all 9,000 products, seed fixed, index 0, default difficulty" if joint else "not requested",
             "rejection_claim_limit": "A structured refusal proves explicit unsupported-axis handling, not mathematical impossibility."}
    for band in BANDS:
        for axis, (lo, hi) in LIMITS.items():
            for value in range(lo, hi + 1):
                stats["single_axis_attempts"] += 1
                generate_case(module, evidence, scope="single_axis", seed=seed, index=0,
                              band=band, requested={axis: value}, repeat=True)
            for value in (True, float(lo), str(lo), None, [], lo - 1, hi + 1):
                stats["invalid_override_attempts"] += 1
                request = {axis: value}
                try:
                    result = module.generate(seed, 0, difficulty=band, **request)
                except (TypeError, ValueError) as exc:
                    stats["invalid_overrides_rejected"] += 1
                    evidence.case({"scope": "invalid_override", "seed": seed, "sample_index": 0,
                                   "difficulty": band, "requested": request, "status": "expected_rejection",
                                   "exception": type(exc).__name__, "message": str(exc)})
                except Exception as exc:
                    evidence.error("invalid_override_wrong_exception", requested=request, difficulty=band,
                                   exception=type(exc).__name__, message=str(exc))
                else:
                    evidence.error("invalid_override_accepted", requested=request, difficulty=band, input=result)
        stats["invalid_override_attempts"] += 1
        try:
            result = module.generate(seed, 0, difficulty=band, misspelled_axis=1)
        except (TypeError, ValueError):
            stats["invalid_overrides_rejected"] += 1
        except Exception as exc:
            evidence.error("unknown_axis_wrong_exception", difficulty=band, exception=type(exc).__name__, message=str(exc))
        else:
            evidence.error("unknown_axis_accepted", difficulty=band, input=result)
    # Preserve the original concrete silent-underfill regression even without --joint.
    regression = generate_case(module, evidence, scope="baseline_underfill_regression", seed=0, index=0,
                               band=None, requested={"grid_h": 7, "grid_w": 7, "n_pairs": 5},
                               allow_joint_rejection=True, repeat=True)
    stats["baseline_underfill_regression_status"] = regression.get("status") if regression else "invalid"
    if joint:
        for h, w, n, p in itertools.product(range(4, 19), range(4, 19), range(1, 11), range(2, 6)):
            stats["joint_attempts"] += 1
            case = generate_case(module, evidence, scope="joint_axes", seed=seed, index=0, band=None,
                                 requested={"grid_h": h, "grid_w": w, "n_pairs": n, "palette_size": p},
                                 allow_joint_rejection=True)
            if case and case.get("status") == "materialized":
                stats["joint_materialized"] += 1
            elif case and case.get("structured_joint_rejection"):
                stats["joint_structured_rejections"] += 1
        if not stats["joint_materialized"]:
            evidence.error("joint_domain_never_materialized", attempted=stats["joint_attempts"])
    evidence.report["overrides"] = stats


def check_validator(module: Any, evidence: Evidence) -> None:
    base = [[0] * 4 for _ in range(4)]
    base[0][0] = base[1][1] = 2
    bad = {"empty": [], "empty_row": [[]], "ragged": [[0, 2], [0]],
           "blank": [[0] * 4 for _ in range(4)], "all_red": [[2] * 4 for _ in range(4)],
           "too_many_windows": [[2 if (r + c) % 2 == 0 else 0 for c in range(6)] for r in range(6)]}
    for name, value in (("color_too_large", 11), ("negative_color", -1), ("bool_color", True),
                        ("float_color", 2.0), ("string_color", "2"), ("none_color", None)):
        grid = copy.deepcopy(base)
        grid[3][3] = value
        bad[name] = grid
    for name, h, w in (("too_short", 3, 4), ("too_tall", 19, 4), ("too_narrow", 4, 3), ("too_wide", 4, 19)):
        grid = [[0] * w for _ in range(h)]
        grid[0][0] = grid[1][1] = 2
        bad[name] = grid
    saturated = [[1] * 4 for _ in range(4)]
    saturated[0][0] = saturated[1][1] = 2
    saturated[0][1] = saturated[1][0] = 0
    bad["background_not_sparse"] = saturated
    stats = {"negative_cases": len(bad), "rejected": 0, "positive_cases": 2, "accepted": 0}
    for name, grid in bad.items():
        case = evidence.case({"scope": "validator_negative", "name": name, "input": grid})
        ok, result = checked_hook(evidence, getattr(module, "self_check", None), grid, name="self_check", case=case)
        if ok and isinstance(result, list) and result and all(isinstance(x, str) for x in result):
            stats["rejected"] += 1
        elif ok:
            evidence.error("validator_accepted_invalid_or_bad_contract", **case, result=result)
    boundary = [[2 if (r + c) % 2 == 0 else 0 for c in range(4)] for r in range(4)]
    for name, grid in (("one_pair", base), ("exact_half_background", boundary)):
        case = evidence.case({"scope": "validator_positive", "name": name, "input": grid,
                              "independent_observed": independently_observe(grid)})
        ok, result = checked_hook(evidence, getattr(module, "self_check", None), grid, name="self_check", case=case)
        if ok and result == []:
            stats["accepted"] += 1
        elif ok:
            evidence.error("validator_rejected_valid_boundary", **case, result=result)
    evidence.report["validator"] = stats


def deterministic_motifs() -> list[dict[str, Any]]:
    motifs = {
        "nonred_diagonal": [[1, 0], [0, 1]],
        "one_blocked_corner": [[2, 7], [0, 2]],
        "third_red": [[2, 2], [0, 2]],
        "preexisting_green": [[2, 3], [0, 2]],
        "shared_red": [[2, 0, 0], [0, 2, 0], [0, 0, 2]],
        "shared_zero": [[2, 0, 2], [0, 2, 0]],
        "orthogonal_attachment": [[2, 0, 0], [0, 2, 2]],
        "bottom_right": [[2, 0], [0, 2]],
    }
    return [{"scope": "deterministic_motif", "name": name, "input": grid,
             "independent_oracle_output": independent_oracle(grid)} for name, grid in motifs.items()]


def check_racket(evidence: Evidence, root: Path, *, pairs: list[dict[str, Any]],
                 representatives: list[dict[str, Any]], exhaustive: bool) -> None:
    if not (root / "src" / "arcpuzzles" / "catalog.py").is_file() or not (root / "catalog").is_dir():
        evidence.error("requested_racket_unavailable", reason="Public Catalog.apply requires the library layout", root=str(root))
        evidence.report["racket"] = {"requested": True, "executed": False, "status": "unavailable"}
        return
    sys.path.insert(0, str(root / "src"))
    from arcpuzzles.catalog import Catalog

    inputs = deterministic_motifs()
    for pair in pairs:
        inputs.append({"scope": "canonical", **{k: pair[k] for k in ("variant", "split", "pair_index")},
                       "input": pair["input"], "stored_output": pair["output"],
                       "independent_oracle_output": independent_oracle(pair["input"])})
    for case in representatives:
        inputs.append({k: case[k] for k in ("scope", "seed", "sample_index", "difficulty", "input", "independent_oracle_output")})
    if exhaustive:
        for index, cells in enumerate(itertools.product((0, 2, 7), repeat=6)):
            grid = [list(cells[:3]), list(cells[3:])]
            inputs.append({"scope": "exhaustive_2x3_027", "enumeration_index": index,
                           "input": grid, "independent_oracle_output": independent_oracle(grid)})
    stats = {"requested": True, "executed": False, "planned_inputs": len(inputs),
             "returned_inputs": 0, "oracle_matches": 0, "stored_canonical_matches": 0,
             "exhaustive_domain": "all 729 2x3 inputs over ordered palette [0,2,7]" if exhaustive else None,
             "batch_size_limit": 64, "batches": [], "source": "public Catalog.apply(reference='canonical')"}
    catalog = Catalog(root)
    with gzip.open(evidence.output / "racket_batches.jsonl.gz", "wt", encoding="utf-8") as receipts:
        for offset in range(0, len(inputs), 64):
            batch = inputs[offset:offset + 64]
            try:
                receipt = catalog.apply(TASK_ID, [case["input"] for case in batch], reference="canonical", timeout=120)
            except Exception as exc:
                evidence.error("racket_batch_exception", batch_offset=offset, grids=[case["input"] for case in batch],
                               exception=type(exc).__name__, message=str(exc), traceback=traceback.format_exc())
                continue
            receipts.write(json.dumps({"batch_offset": offset, "cases": batch, "receipt": receipt}, sort_keys=True) + "\n")
            stats["executed"] = True
            results = receipt.get("results")
            metadata = {k: v for k, v in receipt.items() if k != "results"}
            stats["batches"].append({"offset": offset, "input_count": len(batch), **metadata})
            if not isinstance(results, list) or len(results) != len(batch):
                evidence.error("racket_batch_cardinality", batch_offset=offset, expected_count=len(batch), receipt=receipt)
                continue
            if not receipt.get("rule_hash_matches_catalog"):
                evidence.error("racket_rule_hash_mismatch", batch_offset=offset, receipt=metadata)
            for case, result in zip(batch, results):
                stats["returned_inputs"] += 1
                actual = result.get("output")
                if actual == case["independent_oracle_output"]:
                    stats["oracle_matches"] += 1
                else:
                    evidence.error("racket_oracle_disagreement", **case, output=actual, result=result)
                if "stored_output" in case:
                    if actual == case["stored_output"]:
                        stats["stored_canonical_matches"] += 1
                    else:
                        evidence.error("racket_stored_canonical_disagreement", **case, output=actual, result=result)
            print(f"contract_probe: Racket {min(offset + len(batch), len(inputs))}/{len(inputs)}", file=sys.stderr, flush=True)
    if stats["returned_inputs"] != len(inputs):
        evidence.error("racket_incomplete", planned=len(inputs), returned=stats["returned_inputs"])
    evidence.report["racket"] = stats


def finalize_evidence(evidence: Evidence, *, source_paths: dict[str, Path],
                      snapshots_before: dict[str, Any], started: float) -> None:
    """Write the final report, keeping closed compressed evidence immutable."""
    try:
        snapshots_after = source_snapshot(source_paths)
        evidence.report["source_snapshot_after"] = snapshots_after
        evidence.report["source_snapshot_matches"] = snapshots_before == snapshots_after
        evidence.report["generator_sha256_after"] = snapshots_after["generator"]["sha256"]
        if snapshots_before != snapshots_after:
            evidence.error("source_changed_during_probe", before=snapshots_before, after=snapshots_after)
    except Exception as exc:
        evidence.error("source_snapshot_exception", exception=type(exc).__name__, message=str(exc))
        evidence.report["source_snapshot_matches"] = False
    evidence.close()
    artifact_names = ["cases.jsonl.gz", "racket_batches.jsonl.gz", "failures.jsonl.gz"]
    artifact_metadata = {}
    for filename in artifact_names:
        path = evidence.output / filename
        if not path.exists():
            continue
        try:
            artifact_metadata[filename] = compressed_artifact_metadata(path)
        except Exception as exc:
            evidence.error("compressed_artifact_verification_failed", filename=filename,
                           exception=type(exc).__name__, message=str(exc))
    evidence.report["compressed_evidence"] = {
        "artifacts": artifact_metadata,
        "restore_instructions": "Run each restore_command from the report directory. "
                                "The uncompressed SHA-256 and byte count identify the exact restored bytes; "
                                "the compressed SHA-256 identifies the supplied .gz file.",
        "integrity_instructions": "Compare sha256sum of the .gz files before restoring, then sha256sum "
                                  "and wc -c of restored files against the corresponding metadata.",
        "failure_record_locations": "Failures before stream closure are in failures.jsonl.gz. "
                                    "Failures during finalization are retained in this report's "
                                    "finalization_failures; closed compressed evidence is never rewritten.",
    }
    evidence.report.update({"finished_utc": datetime.now(timezone.utc).isoformat(),
                            "elapsed_seconds": round(time.monotonic() - started, 3),
                            "case_count": evidence.case_count, "error_count": evidence.failure_count,
                            "error_counts": dict(evidence.error_counts),
                            "first_failure_summaries": evidence.failure_examples,
                            "finalization_failures": evidence.finalization_failures,
                            "warnings": evidence.warnings, "passed": evidence.failure_count == 0})
    (evidence.output / "report.json").write_text(
        json.dumps(evidence.report, sort_keys=True, indent=2, default=repr) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, required=True, help="new evidence directory (must not exist)")
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--joint", action="store_true", help="all 9,000 exact-axis requests in default band")
    parser.add_argument("--racket", action="store_true", help="public Catalog.apply authority parity")
    parser.add_argument("--exhaustive-racket", action="store_true", help="also all 729 2x3 grids over {0,2,7}")
    parser.add_argument("--require-teaching-support", action="store_true", help="require two distinct refuting demos per shortcut and rotation")
    args = parser.parse_args(argv)
    if args.per_band < 4:
        parser.error("--per-band must be at least 4 so actual lesson rotations can be checked")
    destination = args.out.resolve()
    if destination.exists():
        parser.error("--out must be a new path; refusing to overwrite existing evidence")
    started = time.monotonic()
    evidence = Evidence(destination)
    root = find_root(__file__)
    generator_path = Path(__file__).resolve().parent.parent / "generator.py"
    source_paths = {"generator": generator_path, "probe": Path(__file__).resolve(),
                    "canonical_ledger": canonical_path(root)}
    snapshots_before = source_snapshot(source_paths)
    source_before = snapshots_before["generator"]["sha256"]
    evidence.report = {
        "schema": "e82-contract-probe-v1", "task_id": TASK_ID,
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "command": [sys.executable, *sys.argv], "root": str(root),
        "probe_sha256": file_digest(Path(__file__).resolve()), "generator_sha256": source_before,
        "source_snapshot_before": snapshots_before,
        "sampling": {"seed": args.seed, "default_sample_indices_inclusive": [0, args.per_band - 1],
                     "bands": list(BANDS), "single_override_seed": args.seed, "single_override_index": 0,
                     "joint_seed": args.seed, "joint_index": 0, "joint_band": None},
        "independent_contract_limits": {key: list(value) for key, value in LIMITS.items()},
        "oracle_authority": "Independent Python diagnostic; not authoritative without the separately reported Racket checks.",
        "racket": {"requested": False, "executed": False, "status": "not requested"},
        "artifacts": {"cases": "cases.jsonl.gz", "full_failures": "failures.jsonl.gz",
                      "racket_receipts_when_requested": "racket_batches.jsonl.gz"},
    }
    try:
        spec = importlib.util.spec_from_file_location("e82_contract_probe_selected_generator", generator_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot import selected generator {generator_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        selected_rows = []
        with canonical_path(root).open(encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    selected_rows.append(row)
        evidence.report["canonical_selected_rows_sha256"] = digest(selected_rows)
        evidence.report["generator_version"] = getattr(module, "VERSION", None)
        evidence.report["declared_rule_hash"] = getattr(module, "RULE_HASH", None)
        rules = rule_registries(module, evidence)
        evidence.report["declared_rules"] = sorted(rules)
        pairs = check_canonical(module, evidence, rules, root)
        representatives = check_defaults(module, evidence, rules, seed=args.seed,
                                         per_band=args.per_band, require_teaching_support=args.require_teaching_support)
        check_override_axes(module, evidence, seed=args.seed, joint=args.joint)
        check_validator(module, evidence)
        if args.racket or args.exhaustive_racket:
            check_racket(evidence, root, pairs=pairs, representatives=representatives, exhaustive=args.exhaustive_racket)
    except Exception as exc:
        evidence.error("unhandled_probe_exception", exception=type(exc).__name__, message=str(exc),
                       traceback=traceback.format_exc())
    finally:
        finalize_evidence(evidence, source_paths=source_paths, snapshots_before=snapshots_before, started=started)
    print(json.dumps({"report": str(destination / "report.json"), "passed": evidence.failure_count == 0,
                      "errors": evidence.failure_count, "elapsed_seconds": evidence.report["elapsed_seconds"]}))
    return 1 if evidence.failure_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
