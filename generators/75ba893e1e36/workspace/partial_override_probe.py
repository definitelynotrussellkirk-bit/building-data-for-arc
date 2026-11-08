#!/usr/bin/env python3
"""Falsify partial-request incompatibility using bounded explicit completions.

Supported exact controls are grid_h, grid_w, palette_size (observed through the
public observe_overrides hook and independently measured pixels), plus literal
palette membership checked from the grid. Raw row strings are rejected before
normalization, and self_check receives the actual raw return. Texture/density priors are intentionally unsupported. A successful complete
request disproves the rejected partial request's claimed incompatibility. Finding
no witness is inconclusive; it does not prove that the request is impossible.

Packet example, from the directory containing review.py:
  python3 review.py run ../.venv-review/bin/python \
    generators/75ba893e1e36/workspace/partial_override_probe.py \
    --task-id 75ba893e1e36 --request '{"grid_h":1,"palette_size":3}' \
    --free-axis grid_w --candidates '[2,4]' --seed-start 0 --seed-count 200 \
    --sample-index 1 --band medium --out ../checks/partial-overrides/replay

--generator-source explicitly selects an authoring snapshot, never a runtime
alias or production selection. The default uses load_selected_generator().
Exit codes: 1 = counterexample/invalid returned input; 2 = inconclusive or error;
0 = every original request returned a validated grid (no rejections observed).
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shlex
import sys
import traceback
import types

from reviewer_support import find_root, load_selected_generator, normalize_grid

EXACT_SCALAR_AXES = frozenset({"grid_h", "grid_w", "palette_size"})
SUPPORTED_AXES = EXACT_SCALAR_AXES | {"palette"}
MAX_GENERATE_CALLS = 2000


def validate_plan(request, free_axis, candidates, seeds):
    if not isinstance(request, dict) or not request:
        raise ValueError("request must be a nonempty JSON object")
    unsupported = set(request) - SUPPORTED_AXES
    if unsupported:
        raise ValueError(f"unsupported exact-control claims: {sorted(unsupported)}")
    if free_axis not in EXACT_SCALAR_AXES:
        raise ValueError("free-axis must be grid_h, grid_w, or palette_size")
    if request.get(free_axis) is not None:
        raise ValueError("free-axis is already fixed by the partial request")
    if not isinstance(candidates, list) or not candidates or any(type(value) is not int for value in candidates):
        raise ValueError("candidates must be a nonempty JSON array of literal integers")
    if len(set(candidates)) != len(candidates):
        raise ValueError("candidate values must be distinct")
    if not seeds or any(type(seed) is not int for seed in seeds):
        raise ValueError("a nonempty integer seed range is required")
    if len(seeds) * (1 + len(candidates)) > MAX_GENERATE_CALLS:
        raise ValueError(f"worst-case call budget exceeds {MAX_GENERATE_CALLS}")
    for name, value in request.items():
        if value is None:
            continue
        if name in EXACT_SCALAR_AXES and type(value) is not int:
            raise ValueError(f"{name} must be a literal integer for an exact-control claim")
        if name == "palette" and (not isinstance(value, list) or not value or
                                  any(type(color) is not int or not 0 <= color <= 9 for color in value) or
                                  len(set(value)) != len(value)):
            raise ValueError("palette must contain distinct literal integer ARC colors")


def validate_return(module, grid, request, band):
    errors = []
    supported = True
    try:
        # Validate the actual return before any normalization can hide its type.
        findings = module.self_check(deepcopy(grid), difficulty=band)
        if not isinstance(findings, (list, tuple)) or any(not isinstance(item, str) for item in findings):
            raise ValueError("self_check must return list[str]")
        errors.extend(findings)
        if not isinstance(grid, (list, tuple)) or not grid:
            raise ValueError("raw generator return must be a nonempty grid sequence")
        if any(not isinstance(row, (list, tuple)) or not row for row in grid):
            raise ValueError("raw generator rows must be nonempty list/tuple rows, not row strings")
        normalized = normalize_grid([list(row) for row in grid])
        literal_metrics = {
            "grid_h": len(normalized), "grid_w": len(normalized[0]),
            "palette_size": len({cell for row in normalized for cell in row}),
        }
        observed = module.observe_overrides(deepcopy(grid))
        if not isinstance(observed, dict):
            raise ValueError("observe_overrides must return a dictionary")
        # The generator's observer is an additional claim, never the pixel oracle.
        for name, actual in literal_metrics.items():
            if name in observed and (type(observed[name]) is not int or observed[name] != actual):
                errors.append(f"observe_overrides claims {name}={observed[name]!r}; literal grid has {actual!r}")
        for name, value in request.items():
            if value is None:
                continue
            if name == "palette":
                actual = sorted({cell for row in normalized for cell in row})
                if actual != sorted(value):
                    errors.append(f"palette requested {sorted(value)!r}, literal grid has {actual!r}")
            else:
                if name not in observed:
                    supported = False
                    errors.append(f"unsupported observable claim: observe_overrides omits {name}")
                actual = literal_metrics[name]
                if type(value) is not int or actual != value:
                    errors.append(f"{name} requested {value!r}, literal grid has {actual!r}")
        return {"valid": not errors, "supported": supported, "errors": errors,
                "observed": observed, "literal_metrics": literal_metrics, "grid": normalized}
    except Exception as exc:
        return {"valid": False, "errors": [*errors, f"{type(exc).__name__}: {exc}"], "grid": grid}


def attempt(module, seed, sample_index, band, request):
    record = {"seed": seed, "sample_index": sample_index, "band": band, "request": deepcopy(request)}
    try:
        grid = module.generate(seed, sample_index, difficulty=band, **deepcopy(request))
    except Exception as exc:
        record.update(status="rejected", error={"type": type(exc).__name__, "message": str(exc),
                      "incompatible_axes": list(getattr(exc, "incompatible_axes", ())),
                      "traceback": traceback.format_exc()})
        return record
    checked = validate_return(module, grid, request, band)
    record.update(status=("unsupported_observable" if not checked.get("supported", True) else
                          "accepted_valid" if checked["valid"] else "accepted_invalid"), validation=checked)
    return record


def run_probe(module, *, request, free_axis, candidates, seeds, sample_index, band):
    seeds = list(seeds)
    validate_plan(request, free_axis, candidates, seeds)
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample-index must be a nonnegative literal integer")
    if not callable(getattr(module, "self_check", None)) or not callable(getattr(module, "observe_overrides", None)):
        raise ValueError("self_check and observe_overrides public hooks are required")
    records = []
    calls = 0
    for seed in seeds:
        original = attempt(module, seed, sample_index, band, request)
        calls += 1
        record = {"original": original, "completions": []}
        if original["status"] == "rejected":
            record["verdict"] = "inconclusive_no_feasible_completion_found"
            for value in candidates:
                completed_request = {**request, free_axis: value}
                completion = attempt(module, seed, sample_index, band, completed_request)
                calls += 1
                record["completions"].append(completion)
                if completion["status"] == "accepted_valid":
                    record["verdict"] = "false_incompatibility_falsified"
                    record["first_feasible_completion"] = completion
                    break
        elif original["status"] == "unsupported_observable":
            record["verdict"] = "unsupported_observable_claim"
        elif original["status"] == "accepted_invalid":
            record["verdict"] = "invalid_original_return"
        else:
            record["verdict"] = "original_request_valid"
        records.append(record)
    counts = {
        "original_requests": len(records), "generator_calls": calls,
        "original_rejections": sum(row["original"]["status"] == "rejected" for row in records),
        "falsified_rejections": sum(row["verdict"] == "false_incompatibility_falsified" for row in records),
        "inconclusive_rejections": sum(row["verdict"].startswith("inconclusive") for row in records),
        "unsupported_observable_claims": sum(row["verdict"] == "unsupported_observable_claim" for row in records),
        "invalid_original_returns": sum(row["verdict"] == "invalid_original_return" for row in records),
        "invalid_candidate_returns": sum(c["status"] == "accepted_invalid" for row in records for c in row["completions"]),
    }
    if counts["falsified_rejections"] or counts["invalid_original_returns"]:
        status, exit_code = "counterexample_found", 1
    elif counts["unsupported_observable_claims"]:
        status, exit_code = "unsupported_observable_claim", 2
    elif counts["original_rejections"]:
        status, exit_code = "inconclusive", 2
    else:
        status, exit_code = "no_rejections_observed", 0
    return {"status": status, "exit_code": exit_code, "counts": counts, "records": records,
            "limitations": ["Only the supplied seeds and candidate values were exercised.",
                            "No witness means inconclusive, not proof of impossibility.",
                            "Observable scalar controls and literal palette membership only; no texture-prior claims.",
                            "This input feasibility probe does not execute or approve reference labels."]}


def load_source(task_id, root, snapshot):
    selected, selected_path, selected_sha = load_selected_generator(task_id, root=root)
    if snapshot is None:
        return selected, selected_path, selected_sha, selected_sha
    source = snapshot.resolve()
    if snapshot.is_symlink() or not source.is_file():
        raise ValueError("generator-source must be an explicit regular source file")
    body = source.read_bytes()
    source_sha = hashlib.sha256(body).hexdigest()
    name = "partial_override_authoring_snapshot_" + source_sha
    module = types.ModuleType(name)
    module.__file__ = str(source)
    # Separate authoring module; no puzzle_generators runtime alias is replaced.
    sys.modules[name] = module
    dependency_root = root / "shared/runtime" if (root / "shared/runtime").is_dir() else root
    previous_path = list(sys.path)
    try:
        sys.path.insert(0, str(dependency_root))
        exec(compile(body, str(source), "exec"), module.__dict__)
    finally:
        sys.path[:] = previous_path
    if getattr(module, "TASK_ID", None) != task_id:
        raise ValueError("authoring snapshot TASK_ID does not match --task-id")
    return module, source, source_sha, selected_sha


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--request", required=True, type=json.loads)
    parser.add_argument("--free-axis", required=True)
    parser.add_argument("--candidates", required=True, type=json.loads)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--seed-count", type=int, default=20)
    parser.add_argument("--sample-index", type=int, default=1)
    parser.add_argument("--band", choices=("easy", "medium", "hard"), default="medium")
    parser.add_argument("--generator-source", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    seeds = list(range(args.seed_start, args.seed_start + args.seed_count))
    validate_plan(args.request, args.free_axis, args.candidates, seeds)
    args.out.mkdir(parents=True, exist_ok=False)
    root = find_root(__file__)
    report = {"schema": "partial-override-feasible-completion-v1", "task_id": args.task_id,
              "command": "python3 review.py run ../.venv-review/bin/python " + shlex.join(sys.argv),
              "outer_cwd": str(root.parent.parent), "payload_cwd": str(Path.cwd()),
              "arguments": {key: str(value) if isinstance(value, Path) else value for key, value in vars(args).items()},
              "tool_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "source_mode": "authoring_snapshot" if args.generator_source else "selected_generator"}
    try:
        module, source, source_sha, selected_sha = load_source(args.task_id, root, args.generator_source)
        report.update(generator_source=str(source), executed_generator_sha256=source_sha,
                      selected_generator_sha256=selected_sha, version=getattr(module, "VERSION", None))
        (args.out / "generator.snapshot.py").write_bytes(source.read_bytes())
        (args.out / "partial_override_probe.snapshot.py").write_bytes(Path(__file__).read_bytes())
        report.update(run_probe(module, request=args.request, free_axis=args.free_axis,
                                candidates=args.candidates, seeds=seeds,
                                sample_index=args.sample_index, band=args.band))
        if hashlib.sha256(source.read_bytes()).hexdigest() != source_sha:
            raise ValueError("executed source changed while probing")
    except Exception as exc:
        report.update(status="error", exit_code=2, error={"type": type(exc).__name__, "message": str(exc),
                                                        "traceback": traceback.format_exc()})
    report["artifact_sha256"] = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                                  for path in sorted(args.out.iterdir()) if path.is_file()}
    (args.out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: report.get(key) for key in ("status", "exit_code", "counts", "executed_generator_sha256", "error")}, sort_keys=True))
    return report["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
