#!/usr/bin/env python3
"""Exhaust consecutive lesson starts and query rotations for this generator.

Run through the packet's run_with_racket.py, or from this independent library
with its Python dependencies and Racket available.  This is an authoring tool:
its JSON report contains canonical and generated reference answers.

Inputs come from direct consecutive generate() calls.  Invalid or duplicate
pairs fail; this tool does not emulate production sampler retries.  Use the
shared lesson-census separately to exercise actual production sampling.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import time
import traceback


TASK_ID = "a06827026857"
HERE = Path(__file__).resolve().parent
STARTS = (0, 1, 2, 3)
DECLARATIONS = ("SEMANTIC_RIVALS", "CANONICAL_SHORTCUTS", "LESSON_COMPETITORS")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def file_digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def load_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def own_support():
    # Search only this file's ancestors, never another checkout or ambient data.
    for parent in HERE.parents:
        for relative in ("shared/runtime/reviewer_support.py", "reviewer_support.py"):
            path = parent / relative
            if path.is_file():
                support = load_file("_a06827026857_probe_support", path)
                return support, path, support.find_root(__file__)
    raise FileNotFoundError("No reviewer_support.py in this tool's own tree")


def grid(value):
    if (not isinstance(value, list) or not 1 <= len(value) <= 30
            or any(not isinstance(row, list) for row in value)
            or not 1 <= len(value[0]) <= 30
            or any(len(row) != len(value[0]) for row in value)
            or any(type(color) is not int or not 0 <= color <= 9 for row in value for color in row)):
        raise ValueError("Expected a rectangular 1..30 by 1..30 integer grid with colors 0..9")
    return deepcopy(value)


def checkpoint(report, out):
    out.parent.mkdir(parents=True, exist_ok=True)
    temporary = out.with_name(out.name + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(out)


def error(report, stage, message, **context):
    item = {"stage": stage, "message": str(message), **context}
    report["errors"].append(item)
    if report["first_error"] is None:
        report["first_error"] = item


def declarations(module):
    problems, rules, names = [], {}, {}
    if type(getattr(module, "EXAMPLES_NEEDED", None)) is not int or module.EXAMPLES_NEEDED != 3:
        problems.append("EXAMPLES_NEEDED must be the integer 3")
    for attr in ("generate", "self_check"):
        if not callable(getattr(module, attr, None)):
            problems.append(f"Missing callable {attr}")
    for attr in DECLARATIONS:
        raw = getattr(module, attr, None)
        if not isinstance(raw, dict) or not raw:
            problems.append(f"{attr} must be a nonempty dict[str, callable]")
            continue
        names[attr] = []
        for name, fn in raw.items():
            if not isinstance(name, str) or not name.strip() or not callable(fn):
                problems.append(f"Malformed {attr} entry {name!r}: expected a nonempty string and callable")
                continue
            key = f"{attr}:{name}"
            rules[key] = fn
            names[attr].append(name)
        names[attr].sort()
    if problems:
        raise ValueError("; ".join(problems))
    return dict(sorted(rules.items())), names


def run(report, args, out):
    support, support_path, root = own_support()
    for path in (root / "shared/runtime", root / "src"):
        if path.is_dir():
            sys.path.insert(0, str(path))
    from arcpuzzles import Catalog

    generator_path = HERE.parent / "generator.py"
    report["sources"] = {
        "library_root": str(root), "generator_path": str(generator_path.relative_to(root)),
        "generator_sha256": file_digest(generator_path), "probe_path": str(Path(__file__).resolve().relative_to(root)),
        "probe_sha256": file_digest(__file__), "reviewer_support_path": str(support_path.relative_to(root)),
        "reviewer_support_sha256": file_digest(support_path),
    }
    module = load_file("_a06827026857_lesson_probe_generator", generator_path)
    rivals, names = declarations(module)
    report["contracts"] = {
        "EXAMPLES_NEEDED": module.EXAMPLES_NEEDED, "declarations": names,
        "rivals": {name: {"module": getattr(fn, "__module__", None), "qualname": getattr(fn, "__qualname__", None)} for name, fn in rivals.items()},
        "namespaces_preserved": True,
    }
    catalog = Catalog(root)
    row = catalog.describe(TASK_ID)
    if (root / row["generator"]).resolve() != generator_path.resolve():
        raise ValueError("Catalog generator path differs from this tool's adjacent generator.py")
    if row["generator_sha256"] != report["sources"]["generator_sha256"]:
        raise ValueError("Generator changed during import/catalog lookup")

    canonical = support.canonical_pairs(TASK_ID, root=root, labeled_only=True)
    if not canonical:
        raise ValueError("Canonical labeled-pair set is empty")
    report["sources"]["canonical_labeled_pairs_sha256"] = digest(canonical)
    inputs = report["unique_inputs"]

    def add_input(inp, origin):
        inp = grid(inp)
        key = digest(inp)
        if key not in inputs:
            inputs[key] = {"input": inp, "origins": [], "output": None}
        elif inputs[key]["input"] != inp:
            raise ValueError("Input digest collision")
        inputs[key]["origins"].append(origin)
        return key

    for pair in canonical:
        identity = {key: pair[key] for key in ("variant", "split", "pair_index")}
        key = add_input(pair["input"], {"kind": "canonical", **identity})
        report["canonical_pairs"].append({**identity, "input_sha256": key, "canonical_output": grid(pair["output"]), "canonical_output_sha256": digest(pair["output"])})

    # One orthogonal appendage changes a corner's degree from two to three.
    # This witness is scored dynamically; there is no copied list of rivals.
    corner = [[0] * 5 for _ in range(5)]
    for r in range(1, 4):
        for c in range(1, 4):
            corner[r][c] = 4
    corner[1][0] = 4
    witness_key = add_input(corner, {"kind": "witness", "name": "one_corner_appendage"})
    report["witnesses"]["one_corner_appendage"] = {"input_sha256": witness_key}

    draws = {}
    for band in args.bands:
        for seed in args.seeds:
            for index in range(max(STARTS) + 4):
                identity = {"difficulty": band, "seed": seed, "sample_index": index}
                try:
                    inp = grid(module.generate(seed=seed, sample_index=index, difficulty=band))
                    repeated = grid(module.generate(seed=seed, sample_index=index, difficulty=band))
                    if repeated != inp:
                        raise ValueError("generate is not deterministic for identical arguments")
                    reasons = module.self_check(deepcopy(inp), difficulty=band)
                    if not isinstance(reasons, (list, tuple)) or any(not isinstance(reason, str) for reason in reasons):
                        raise TypeError("self_check must return list[str]")
                    if reasons:
                        raise ValueError("self_check rejected input: " + "; ".join(reasons))
                    key = add_input(inp, {"kind": "generated", **identity})
                    draw = {**identity, "input_sha256": key, "status": "generated"}
                    draws[(band, seed, index)] = draw
                    report["draws"].append(draw)
                except Exception as exc:
                    error(report, "generation", f"{type(exc).__name__}: {exc}", **identity)
            checkpoint(report, out)

    keys = list(inputs)
    bound_rule = None
    for offset in range(0, len(keys), args.batch_size):
        batch_keys = keys[offset:offset + args.batch_size]
        if file_digest(generator_path) != report["sources"]["generator_sha256"]:
            raise ValueError("Generator source changed during the probe")
        result = catalog.apply(TASK_ID, [inputs[key]["input"] for key in batch_keys], reference="canonical", timeout=args.timeout)
        receipt = {key: value for key, value in result.items() if key != "results"}
        receipt["input_sha256s"] = batch_keys
        report["reference_batches"].append(receipt)
        identity = {key: result.get(key) for key in ("task_id", "rule_task_id", "reference", "rule_file", "executed_rule_hash", "catalog_rule_hash", "rule_text_sha256", "generator_sha256")}
        if (identity["task_id"] != TASK_ID or identity["rule_task_id"] != TASK_ID
                or identity["reference"] != "canonical" or not result.get("rule_hash_matches_catalog")
                or identity["generator_sha256"] != report["sources"]["generator_sha256"]
                or not identity["rule_text_sha256"] or not identity["executed_rule_hash"]):
            raise ValueError("Racket apply returned missing or mismatched source/rule identities")
        if bound_rule is not None and identity != bound_rule:
            raise ValueError("Reference source/rule identities changed between label batches")
        bound_rule = identity
        report["sources"]["reference"] = identity
        results = result.get("results")
        if not isinstance(results, list) or len(results) != len(batch_keys):
            raise ValueError("Racket apply returned a short or malformed result batch")
        for key, labeled in zip(batch_keys, results, strict=True):
            if labeled.get("input") != inputs[key]["input"] or not labeled.get("valid_output") or labeled.get("error"):
                raise ValueError(f"Invalid Racket result for {key}: {labeled.get('error')}")
            output = grid(labeled.get("output"))
            inputs[key].update(output=output, output_sha256=digest(output),
                               apply_input_sha256=labeled.get("input_sha256"), apply_output_sha256=labeled.get("output_sha256"))
        checkpoint(report, out)
        print(f"Labeled {min(offset + args.batch_size, len(keys))}/{len(keys)} unique inputs", file=sys.stderr, flush=True)

    cache = {}
    predictions = report["rival_predictions"]
    for name, fn in rivals.items():
        predictions[name] = {}
        for key, pair in inputs.items():
            cache_key = (id(fn), key)
            if cache_key not in cache:
                try:
                    predicted = grid(fn(deepcopy(pair["input"])))
                    if grid(fn(deepcopy(pair["input"]))) != predicted:
                        raise ValueError("Rival is not deterministic for identical inputs")
                    cache[cache_key] = {"output": predicted, "output_sha256": digest(predicted), "matches_reference": predicted == pair["output"]}
                except Exception as exc:
                    cache[cache_key] = {"error": f"{type(exc).__name__}: {exc}"}
            predictions[name][key] = cache[cache_key]
            if "error" in cache[cache_key]:
                error(report, "rival_prediction", cache[cache_key]["error"], rival=name, input_sha256=key)

    for pair in report["canonical_pairs"]:
        key = pair["input_sha256"]
        pair["reference_matches_canonical"] = inputs[key]["output"] == pair["canonical_output"]
        if not pair["reference_matches_canonical"]:
            error(report, "canonical_reference", "Executed Racket output disagrees with canonical label", variant=pair["variant"], split=pair["split"], pair_index=pair["pair_index"], input_sha256=key)
    for name in rivals:
        fits = []
        for pair in report["canonical_pairs"]:
            prediction = predictions[name][pair["input_sha256"]]
            fits.append({"variant": pair["variant"], "split": pair["split"], "pair_index": pair["pair_index"], "exact": prediction.get("output") == pair["canonical_output"], "error": prediction.get("error")})
        fit = {"pair_count": len(fits), "exact_count": sum(item["exact"] for item in fits), "fits_all": all(item["exact"] and not item["error"] for item in fits), "pairs": fits}
        report["canonical_rival_fit"][name] = fit
        if name.startswith("CANONICAL_SHORTCUTS:") and not fit["fits_all"]:
            error(report, "canonical_shortcut_contract", "Declared canonical shortcut does not fit all labeled canonical pairs", rival=name)
        pred = predictions[name][witness_key]
        report["witnesses"]["one_corner_appendage"].setdefault("rivals", {})[name] = {"refuted": pred.get("matches_reference") is False, "error": pred.get("error"), "prediction_sha256": pred.get("output_sha256")}

    def score(pair_keys, query_position, lesson_identity):
        demo_positions = [position for position in range(4) if position != query_position]
        rival_statuses, ambiguous = {}, []
        for name in rivals:
            rows = [predictions[name][key] for key in pair_keys]
            if any("error" in value for value in rows):
                status = "error"
            elif not all(rows[position]["matches_reference"] for position in demo_positions):
                status = "refuted"
            elif rows[query_position]["matches_reference"]:
                status = "survived_all"
            else:
                status = "ambiguous"
                ambiguous.append(name)
                if report["first_ambiguity"] is None:
                    report["first_ambiguity"] = {
                        **lesson_identity, "query_position": query_position, "demo_positions": demo_positions, "rival": name,
                        "train": [{"input": inputs[pair_keys[position]]["input"], "output": inputs[pair_keys[position]]["output"]} for position in demo_positions],
                        "query": {"input": inputs[pair_keys[query_position]]["input"], "output": inputs[pair_keys[query_position]]["output"]},
                        "rival_prediction": rows[query_position]["output"],
                    }
            rival_statuses[name] = status
        return {"query_position": query_position, "demo_positions": demo_positions, "query_sample_index": lesson_identity["start_index"] + query_position,
                "demo_sample_indices": [lesson_identity["start_index"] + position for position in demo_positions],
                "rivals": rival_statuses, "ambiguous_rivals": ambiguous,
                "status": "error" if "error" in rival_statuses.values() else ("ambiguous" if ambiguous else "no_ambiguity_found")}

    for band in args.bands:
        for seed in args.seeds:
            for start in STARTS:
                identity = {"difficulty": band, "seed": seed, "start_index": start}
                try:
                    sample_indices = list(range(start, start + 4))
                    pair_keys = [draws[(band, seed, index)]["input_sha256"] for index in sample_indices]
                    if len(set(pair_keys)) != 4:
                        raise ValueError("Duplicate inputs within a four-pair direct lesson; production sampler could advance indices")
                    rotations = [score(pair_keys, position, identity) for position in range(4)]
                    report["lessons"].append({**identity, "sample_indices": sample_indices, "input_sha256s": pair_keys,
                                              "output_sha256s": [inputs[key]["output_sha256"] for key in pair_keys],
                                              "instance_sha256": digest([{field: inputs[key][field] for field in ("input", "output")} for key in pair_keys]),
                                              "production_query_position": 3, "production": rotations[3], "rotations": rotations})
                except Exception as exc:
                    error(report, "lesson_assembly", f"{type(exc).__name__}: {exc}", **identity)
            checkpoint(report, out)
    if file_digest(generator_path) != report["sources"]["generator_sha256"] or file_digest(__file__) != report["sources"]["probe_sha256"]:
        error(report, "source_binding", "Generator or probe changed while the probe was running")


def summarize(report):
    lessons = report["lessons"]
    rotations = [rotation for lesson in lessons for rotation in lesson["rotations"]]
    generated_keys = {draw["input_sha256"] for draw in report["draws"]}
    summary = {
        "requested_lessons": report["request"]["expected_lessons"], "materialized_lessons": len(lessons),
        "requested_rotations": report["request"]["expected_rotations"], "materialized_rotations": len(rotations),
        "canonical_pairs": len(report["canonical_pairs"]), "generated_draws": len(report["draws"]),
        "unique_generated_inputs": len(generated_keys), "unique_inputs_labeled": sum(pair["output"] is not None for pair in report["unique_inputs"].values()),
        "unique_output_grids": len({pair["output_sha256"] for pair in report["unique_inputs"].values() if pair["output"] is not None}),
        "production_statuses": dict(Counter(lesson["production"]["status"] for lesson in lessons)),
        "rotation_statuses": dict(Counter(rotation["status"] for rotation in rotations)),
        "rival_counts": {}, "error_count": len(report["errors"]),
    }
    for name in report.get("contracts", {}).get("rivals", {}):
        summary["rival_counts"][name] = {
            "production": dict(Counter(lesson["production"]["rivals"][name] for lesson in lessons)),
            "rotations": dict(Counter(rotation["rivals"][name] for rotation in rotations)),
        }
    report["summary"] = summary
    complete = len(lessons) == summary["requested_lessons"] and len(rotations) == summary["requested_rotations"]
    report["coverage"] = "complete_requested_starts_and_rotations" if complete else "incomplete"
    if not complete and not report["errors"]:
        error(report, "coverage", "Requested lessons or rotations were not all materialized")
        summary["error_count"] = len(report["errors"])
    report["status"] = "error" if report["errors"] else ("ambiguous" if report["first_ambiguity"] else "no_ambiguity_found")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, nargs="+", default=list(range(8)), metavar="SEED", help="Explicit distinct seeds; default: 0 1 2 3 4 5 6 7")
    parser.add_argument("--bands", nargs="+", choices=("easy", "medium", "hard"), default=["easy", "medium", "hard"])
    parser.add_argument("--out", type=Path, default=HERE / "lesson-window-evidence.json", help="New report path; relative paths use the current working directory")
    parser.add_argument("--batch-size", type=int, default=64, help="Unique inputs per Catalog.apply call, 1..64")
    parser.add_argument("--timeout", type=float, default=180, help="Seconds allowed per Racket label batch")
    args = parser.parse_args()
    if len(set(args.seeds)) != len(args.seeds) or any(seed < 0 or seed >= 2**32 for seed in args.seeds):
        parser.error("--seeds must be distinct integers in [0, 2**32)")
    if len(set(args.bands)) != len(args.bands):
        parser.error("--bands must be distinct")
    if not 1 <= args.batch_size <= 64 or not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("--batch-size must be 1..64 and --timeout must be finite and positive")
    out = args.out.resolve()
    if out.exists() or out.with_name(out.name + ".tmp").exists():
        parser.error("--out and its .tmp checkpoint must be new paths")
    expected = len(args.seeds) * len(args.bands) * len(STARTS)
    report = {
        "schema": "a06827026857-lesson-windows-v1", "task_id": TASK_ID, "status": "incomplete", "started_at": now(),
        "command": [sys.executable, *sys.argv], "cwd": str(Path.cwd()),
        "request": {"seeds": args.seeds, "bands": args.bands, "start_indices": list(STARTS), "demos": 3, "queries": 1,
                    "expected_lessons": expected, "expected_rotations": expected * 4, "batch_size": args.batch_size, "timeout_seconds_per_batch": args.timeout},
        "sampling_mode": "Direct consecutive generate(seed, sample_index, difficulty) assembly; invalid or duplicate lesson pairs fail without sampler retries.",
        "rotation_recipe": "Hold out each of four labeled pairs once; preserve the order of the other three. Position 3 is the original production-layout query.",
        "limits": ["Finite evidence against the currently declared rivals, not proof of universal identifiability.",
                   "This probe does not exercise production rejection/retry sampling; use the shared lesson-census for that.",
                   "Exact input uniqueness is measured by normalized grid hashes, not semantic equivalence.",
                   "Canonical and generated answers are authoring evidence, not visible-only solve data or training admission."],
        "errors": [], "first_error": None, "first_ambiguity": None, "unique_inputs": {}, "draws": [], "lessons": [],
        "canonical_pairs": [], "canonical_rival_fit": {}, "reference_batches": [], "rival_predictions": {}, "witnesses": {},
    }
    started = time.monotonic()
    checkpoint(report, out)
    try:
        run(report, args, out)
    except Exception as exc:
        error(report, "probe", f"{type(exc).__name__}: {exc}", traceback=traceback.format_exc())
    except KeyboardInterrupt:
        error(report, "interrupted", "Probe interrupted; report retains partial evidence")
    summarize(report)
    report.update(finished_at=now(), elapsed_seconds=round(time.monotonic() - started, 3))
    checkpoint(report, out)
    print(json.dumps({"status": report["status"], "coverage": report["coverage"], "summary": report["summary"], "first_error": report["first_error"], "report": str(out)}, indent=2))
    return 2 if report["status"] == "error" else (1 if report["status"] == "ambiguous" else 0)


if __name__ == "__main__":
    raise SystemExit(main())
