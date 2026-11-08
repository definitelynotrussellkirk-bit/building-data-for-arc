#!/usr/bin/env python3
"""Bounded, private, source-bound teaching audit; grants no native acceptance.

Run through WORK/run_with_racket.py with --out pointing to a new directory.
The protected audit checks eight lessons against seven explicit rivals, then a
Python-only sampler sweep checks eighty requests.  Every selected label and every candidate demonstration
prediction is executed through the checkout's protected native evaluator.
Only demonstration survivors are evaluated on queries.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import redirect_stdout
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TASK = "7bba59d92716"
SETTINGS = ({"length_rule": "fixed_five"}, {"length_rule": "marker_size"})
SOURCE_NAMES = ("prototype.py", "adapter.py", "rivals.py", "audit.py", "promotion.json", "canonical.rkt")
LIMITS = (
    "Finite declared settings and seven explicit rivals only; no universal uniqueness claim. "
    "The eighty-request sweep uses independent Python interpretations, not additional Racket replay. "
    "Witnesses are the smallest observed decisive demonstrations, not globally minimized grids. "
    "This reviewer audit grants neither native acceptance nor training admission."
)


def _bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _hash(value):
    return hashlib.sha256(_bytes(value)).hexdigest()


def _text_hash(value):
    return hashlib.sha256(value.encode()).hexdigest()


def _write(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")


def _load(path, suffix):
    name = "_marker_audit_" + suffix + "_" + _text_hash(str(path))[:12]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _sources():
    paths = [HERE / name for name in SOURCE_NAMES]
    paths += [ROOT / f"generators/{TASK}/generator.py", ROOT / "src/arcpuzzles/parametric_worker.py"]
    return {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in paths if path.is_file()}


def _error(report, kind, **details):
    report["errors"].append({"kind": kind, **details})


def _job(seed, demos, settings):
    return {"seed": seed, "demos": demos, "queries": 4, "settings": deepcopy(settings)}


def _episode(prototype, rivals, job, grid):
    settings = deepcopy(job["settings"])
    value = prototype.generate(job["seed"], settings, demos=job["demos"], queries=4)
    if type(value) is not dict or value.get("program_solution") != prototype.program(settings):
        raise ValueError("generation must return the exact selected program_solution")
    result = {"program": value["program_solution"]}
    seen = set()
    for split, count in (("train", job["demos"]), ("test", 4)):
        if type(value.get(split)) is not list or len(value[split]) != count:
            raise ValueError(f"{split} count differs from its independent request")
        result[split] = []
        for pair in value[split]:
            if type(pair) is not dict or not {"input", "output"} <= pair.keys():
                raise ValueError("each pair must contain input and output")
            normalized = {"input": grid(pair["input"]), "output": grid(pair["output"])}
            digest = _hash(normalized["input"])
            if digest in seen:
                raise ValueError("demonstration and query inputs must all be distinct")
            seen.add(digest)
            marker_size = len(rivals.marker_cells(normalized["input"]))
            if marker_size not in (3, 5, 7):
                raise ValueError("marker must contain three, five, or seven cells")
            result[split].append(normalized)
    if [len(rivals.marker_cells(p["input"])) for p in result["train"][:2]] != [3, 7]:
        raise ValueError("the two teaching anchors must have marker sizes three then seven")
    if not any(len(p["input"]) == len(p["input"][0]) == 30 for p in result["test"]):
        raise ValueError("four-query lessons must include their substantive 30x30 case")
    return result


def _metrics(pair, settings, rivals):
    g = pair["input"]
    h, w = len(g), len(g[0])
    cells = [(r, c) for r in range(h) for c in range(w) if g[r][c] != 0]
    blue = rivals.components(g, 1)
    marker = rivals.marker_cells(g)
    changed = [(r, c) for r in range(h) for c in range(w)
               if pair["output"][r][c] != g[r][c]]
    return {
        "input_sha256": _hash(g), "height": h, "width": w,
        "nonzero_cells": len(cells), "density": len(cells) / (h * w),
        "occupied_bbox": [min(r for r, _ in cells), min(c for _, c in cells),
                          max(r for r, _ in cells), max(c for _, c in cells)],
        "occupied_quadrants": sorted({(2 if r >= h // 2 else 0) + (1 if c >= w // 2 else 0)
                                      for r, c in cells}),
        "boundary_nonzero_cells": sum(r in (0, h - 1) or c in (0, w - 1) for r, c in cells),
        "blue_component_count": len(blue),
        "blue_component_sizes": sorted(len(obj) for obj in blue),
        "vertical_blue_lengths": sorted(len(obj) for obj in blue if len({c for _, c in obj}) == 1),
        "marker_size": len(marker),
        "marker_height": max(r for r, _ in marker) - min(r for r, _ in marker) + 1,
        "marker_width": max(c for _, c in marker) - min(c for _, c in marker) + 1,
        "selected_length": rivals.selected_length(g, settings),
        "changed_cells": len(changed),
        "changed_quadrants": sorted({(2 if r >= h // 2 else 0) + (1 if c >= w // 2 else 0)
                                     for r, c in changed}),
    }


def _differences(left, right):
    if len(left) != len(right) or len(left[0]) != len(right[0]):
        return {"shape_mismatch": True}
    return [[r, c, left[r][c], right[r][c]]
            for r in range(len(left)) for c in range(len(left[0])) if left[r][c] != right[r][c]]


def _keep_witness(witnesses, candidate_id, job, index, pair, output, alternate, registry):
    key = candidate_id + "|chosen=" + job["settings"]["length_rule"]
    old = witnesses.get(key)
    area = len(pair["input"]) * len(pair["input"][0])
    if old is not None and old["area"] <= area:
        return
    selected_id = "setting:" + job["settings"]["length_rule"]
    witnesses[key] = {
        "kind": "smallest_observed_decisive_demonstration", "area": area,
        "location": {**job, "split": "train", "pair_index": index},
        "input": pair["input"], "settings": job["settings"],
        "program": registry[selected_id]["program"], "output": output,
        "candidate_id": candidate_id,
        "counterfactual_program": registry[candidate_id]["program"],
        "counterfactual_output": alternate,
        "differing_cells": _differences(output, alternate),
        "racket": {"backend": "racket", "protected": True},
    }


def _sweep(prototype, rivals, grid, report):
    rows, previous_inputs, unique_queries = [], {}, set()
    for seed in range(8):
        for demos in range(2, 7):
            for settings in SETTINGS:
                job = _job(seed, demos, settings)
                entry = {**job, "errors": []}
                try:
                    episode = _episode(prototype, rivals, job, grid)
                    input_hashes = [_hash(p["input"]) for split in ("train", "test") for p in episode[split]]
                    paired_key = (seed, demos)
                    if paired_key in previous_inputs and previous_inputs[paired_key] != input_hashes:
                        entry["errors"].append("inputs differ between parameter settings")
                    previous_inputs[paired_key] = input_hashes
                    for split in ("train", "test"):
                        for index, pair in enumerate(episode[split]):
                            if rivals.reference(pair["input"], settings) != pair["output"]:
                                entry["errors"].append(f"independent intended-rule disagreement at {split}[{index}]")
                    alive = []
                    for name in rivals.NAMES:
                        if all(rivals.predict(name, p["input"], settings) == p["output"] for p in episode["train"]):
                            alive.append(name)
                            for index, pair in enumerate(episode["test"]):
                                if rivals.predict(name, pair["input"], settings) != pair["output"]:
                                    entry["errors"].append(f"Python-only teaching hole: {name} changes query {index}")
                    setting_survivors = [s for s in SETTINGS
                                         if all(rivals.reference(p["input"], s) == p["output"] for p in episode["train"])]
                    if setting_survivors != [settings]:
                        entry["errors"].append("demonstrations do not uniquely select the declared setting")
                    entry["surviving_rivals"] = alive
                    entry["input_hashes"] = input_hashes
                    entry["query_metrics"] = [_metrics(p, settings, rivals) for p in episode["test"]]
                    unique_queries.update(_hash(p["input"]) for p in episode["test"])
                except Exception as exc:
                    entry["errors"].append(f"{type(exc).__name__}: {exc}")
                if entry["errors"]:
                    _error(report, "sampler_sweep", job=job, details=entry["errors"])
                rows.append(entry)
    return {"backend": "independent_python_only", "requests": len(rows),
            "unique_query_inputs": len(unique_queries), "checks": rows}


def run(output):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    initial_sources = _sources()
    report = {
        "schema": "arcpuzzles-marker-line-self-audit-v1", "task_id": TASK,
        "status": "running", "errors": [], "source_sha256": initial_sources,
        "limits": LIMITS, "native_acceptance": False, "training_admitted": False,
        "racket_evaluations": 0, "racket_successful_evaluations": 0,
        "selected_labels_checked": 0, "checks": [],
    }
    registry, witnesses, holes = {}, {}, []
    bridge = None
    try:
        sys.path.insert(0, str(ROOT / "src"))
        from arcpuzzles.catalog import Catalog
        from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator
        runtime = ROOT / "shared/runtime"
        with _local_imports(runtime, HERE):
            from arc_repl.parser import Symbol, parse_all
            prototype = _load(HERE / "prototype.py", "prototype")
            rivals = _load(HERE / "rivals.py", "rivals")
            report["rival_names"] = list(rivals.NAMES)
            report["rival_count"] = len(rivals.NAMES)
            record = Catalog(ROOT).get(TASK)
            canonical = {v["program_solution"] for v in record["variants"] if v.get("program_solution")}
            if canonical != {prototype.program(SETTINGS[0])}:
                raise ValueError("fixed_five must preserve the exact canonical program bytes")
            report["canonical_program_sha256"] = _text_hash(next(iter(canonical)))
            report["canonical_rule_hash"] = record["rule_hash"]
            for settings in SETTINGS:
                key = settings["length_rule"]
                registry["setting:" + key] = {"kind": "declared_setting", "settings": settings,
                                                "program": prototype.program(settings)}
                for name in rivals.NAMES:
                    registry[f"rival:{name}:{key}"] = {
                        "kind": "rival", "name": name, "settings": settings,
                        "description": rivals.DESCRIPTIONS[name], "program": rivals.program(name, settings),
                    }
            for entry in registry.values():
                forms = parse_all(entry["program"])
                if len(forms) != 1 or not isinstance(forms[0], list) or forms[0][0] != Symbol("rule!"):
                    raise ValueError("each registered program must be exactly one standalone rule!")
                entry["program_sha256"] = _text_hash(entry["program"])
            with redirect_stdout(sys.stderr):
                apply, identity, bridge = _real_evaluator(runtime)
            report["racket"] = identity

            def execute(program_id, pair, location):
                report["racket_evaluations"] += 1
                try:
                    actual = _grid(apply(registry[program_id]["program"], deepcopy(pair["input"])))
                    report["racket_successful_evaluations"] += 1
                    return actual
                except Exception as exc:
                    _error(report, "racket_execution", program_id=program_id, location=location,
                           exception=type(exc).__name__, message=str(exc))
                    return None

            paired_inputs = {}
            for seed in (0, 17):
                for demos in (2, 6):
                    for settings in SETTINGS:
                        job = _job(seed, demos, settings)
                        selected_id = "setting:" + settings["length_rule"]
                        try:
                            episode = _episode(prototype, rivals, job, _grid)
                        except Exception as exc:
                            _error(report, "generation", job=job, exception=type(exc).__name__, message=str(exc))
                            continue
                        input_hashes = [_hash(p["input"]) for split in ("train", "test") for p in episode[split]]
                        if (seed, demos) in paired_inputs and paired_inputs[(seed, demos)] != input_hashes:
                            _error(report, "unmatched_setting_inputs", job=job)
                        paired_inputs[(seed, demos)] = input_hashes
                        entry = {**job, "selected_program_id": selected_id, "candidates": [], "pairs": []}
                        truth = {}
                        for split in ("train", "test"):
                            truth[split] = []
                            for index, pair in enumerate(episode[split]):
                                location = {**job, "split": split, "pair_index": index}
                                actual = execute(selected_id, pair, location)
                                truth[split].append(actual)
                                if actual is not None:
                                    report["selected_labels_checked"] += 1
                                    if actual != pair["output"]:
                                        _error(report, "selected_label_disagreement", location=location,
                                               input=pair["input"], claimed=pair["output"], actual=actual)
                                    if actual != rivals.reference(pair["input"], settings):
                                        _error(report, "independent_reference_disagreement", location=location)
                                entry["pairs"].append({"split": split, "pair_index": index,
                                                       **_metrics(pair, settings, rivals)})
                        candidates = ["setting:" + s["length_rule"] for s in SETTINGS if s != settings]
                        candidates += [f"rival:{name}:{settings['length_rule']}" for name in rivals.NAMES]
                        for candidate_id in candidates:
                            candidate = registry[candidate_id]
                            demo_outputs = []
                            for index, pair in enumerate(episode["train"]):
                                location = {**job, "split": "train", "pair_index": index}
                                actual = execute(candidate_id, pair, location)
                                demo_outputs.append(actual)
                                expected = (rivals.predict(candidate["name"], pair["input"], settings)
                                            if candidate["kind"] == "rival"
                                            else rivals.reference(pair["input"], candidate["settings"]))
                                if actual is not None and actual != expected:
                                    _error(report, "rival_python_racket_disagreement", candidate_id=candidate_id,
                                           location=location, actual=actual, expected=expected)
                                if actual is not None and truth["train"][index] is not None and actual != truth["train"][index]:
                                    _keep_witness(witnesses, candidate_id, job, index, pair,
                                                  truth["train"][index], actual, registry)
                            valid = all(value is not None for value in demo_outputs + truth["train"])
                            survives = valid and demo_outputs == truth["train"]
                            comparison = {"program_id": candidate_id, "valid_execution": valid,
                                          "survives_demonstrations": survives,
                                          "demo_disagreement_indices": [i for i, (a, b) in enumerate(zip(demo_outputs, truth["train"]))
                                                                        if a is not None and b is not None and a != b]}
                            if survives:
                                if candidate["kind"] == "declared_setting":
                                    _error(report, "setting_not_identified", job=job, candidate_id=candidate_id)
                                comparison["query_agreement"] = []
                                for index, pair in enumerate(episode["test"]):
                                    location = {**job, "split": "test", "pair_index": index}
                                    actual = execute(candidate_id, pair, location)
                                    expected = (rivals.predict(candidate["name"], pair["input"], settings)
                                                if candidate["kind"] == "rival"
                                                else rivals.reference(pair["input"], candidate["settings"]))
                                    if actual is not None and actual != expected:
                                        _error(report, "rival_python_racket_disagreement", candidate_id=candidate_id,
                                               location=location, actual=actual, expected=expected)
                                    agrees = actual is not None and truth["test"][index] is not None and actual == truth["test"][index]
                                    comparison["query_agreement"].append(agrees)
                                    if actual is not None and truth["test"][index] is not None and not agrees:
                                        hole = {"job": job, "candidate_id": candidate_id, "query_index": index,
                                                "train": episode["train"], "input": pair["input"],
                                                "program": registry[selected_id]["program"],
                                                "output": truth["test"][index],
                                                "counterfactual_program": candidate["program"],
                                                "counterfactual_output": actual,
                                                "racket": {"backend": "racket", "protected": True}}
                                        holes.append(hole)
                                        _error(report, "teaching_hole", job=job, candidate_id=candidate_id, query_index=index)
                            entry["candidates"].append(comparison)
                        report["checks"].append(entry)
                        print(json.dumps({"lesson": job, "completed": len(report["checks"]),
                                          "errors_so_far": len(report["errors"])}), file=sys.stderr, flush=True)
            bridge.close()
            bridge = None
            report["sampler_sweep"] = _sweep(prototype, rivals, _grid, report)
    except Exception as exc:
        _error(report, "audit_exception", exception=type(exc).__name__, message=str(exc))
    finally:
        if bridge is not None:
            bridge.close()
        final_sources = _sources()
        report["source_stable"] = initial_sources == final_sources
        if not report["source_stable"]:
            _error(report, "source_changed_during_audit", final_source_sha256=final_sources)
        report["completed_native_lessons"] = len(report["checks"])
        if report["completed_native_lessons"] != 8:
            _error(report, "incomplete_native_lesson_count", expected=8, actual=len(report["checks"]))
        report["decisive_witness_count"] = len(witnesses)
        report["teaching_hole_count"] = len(holes)
        report["error_counts"] = dict(Counter(e["kind"] for e in report["errors"]))
        report["status"] = "passed_finite_audit" if not report["errors"] else "failed"
        report["private_artifacts"] = {
            "program_registry": "programs.private.json",
            "decisive_demonstrations": "witnesses.private.json",
            "teaching_holes": "holes.private.json",
        }
        _write(output / "programs.private.json", {"programs": registry})
        _write(output / "witnesses.private.json", {"cases": list(witnesses.values())})
        _write(output / "holes.private.json", {"cases": holes})
        _write(output / "audit.json", report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path, help="New private evidence directory; existing paths are refused.")
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error(f"output already exists: {args.out}")
    report = run(args.out)
    print(json.dumps({k: report[k] for k in ("status", "completed_native_lessons", "racket_evaluations",
                                           "selected_labels_checked", "decisive_witness_count",
                                           "teaching_hole_count", "error_counts")}))
    return 0 if report["status"] == "passed_finite_audit" else 1


if __name__ == "__main__":
    raise SystemExit(main())
