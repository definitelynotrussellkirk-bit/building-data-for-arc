#!/usr/bin/env python3
"""Small explicit-case audit of the public generator and GenCtx APIs.

Run through the packet's run_with_racket.py wrapper (no Racket is invoked by
this probe). Pass only cases whose expected disposition you have reviewed:
--case '{"grid_h": 8}' expects acceptance; --reject-case '{...}' expects a
ValueError/TypeError/KeyError. The probe does not infer an axis domain or
replace the shared override matrix, semantic gate, or lesson census.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import inspect
import json
from pathlib import Path
import sys
import types

from puzzle_generators.base import set_ctx_observer


DIMENSIONS = {"grid_h": 0, "grid_w": 1, "height": 0, "width": 1,
              "canvas_h": 0, "canvas_w": 1}
DECLARATIONS = ("AXES", "INCOMPATIBLE_OVERRIDE_COMBINATIONS", "MIN_STRICT_FRAC",
                "EXAMPLES_NEEDED", "SEMANTIC_WITNESSES", "SEMANTIC_RIVALS",
                "WITNESS_RIVALS", "BRANCH_WITNESSES", "LESSON_COMPETITORS",
                "CANONICAL_SHORTCUTS", "SCHEDULE_PROFILES", "RULE_HASH")
HOOKS = ("generate", "self_check", "observe_overrides", "strict_canonical_like",
         "lesson_identifiable", "schedule_profile", "make_degenerate")


def describe(value):
    if callable(value):
        return {"callable": True, "signature": str(inspect.signature(value))}
    if isinstance(value, dict):
        return {str(k): describe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [describe(v) for v in value]
    return value


def invoke_validator(fn, grid, band, overrides):
    parameters = inspect.signature(fn).parameters
    kwargs = {}
    if "difficulty" in parameters:
        kwargs["difficulty"] = band
    if "meta" in parameters:
        kwargs["meta"] = {**overrides, "overrides": dict(overrides)}
    return fn(copy.deepcopy(grid), **kwargs)


def observe(module, grid):
    observations = {}
    if isinstance(grid, list) and grid and isinstance(grid[0], list):
        for name, dimension in DIMENSIONS.items():
            if name in getattr(module, "AXES", {}):
                observations[name] = len(grid) if dimension == 0 else len(grid[0])
    fn = getattr(module, "observe_overrides", None)
    if callable(fn):
        declared = fn(copy.deepcopy(grid))
        if not isinstance(declared, dict):
            raise TypeError("observe_overrides must return a dict")
        for axis, value in observations.items():
            if axis in declared and declared[axis] != value:
                raise ValueError(f"observer reports {axis}={declared[axis]!r}, dimension is {value}")
        observations.update(declared)
    return observations


def probe_draw(module, band, seed, index, overrides, expect):
    row = {"difficulty": band, "seed": seed, "sample_index": index,
           "overrides": overrides, "expected": expect, "findings": []}
    contexts = []
    set_ctx_observer(contexts.append)
    try:
        grid = module.generate(seed, index, difficulty=band, **overrides)
    except Exception as exc:
        row["disposition"] = "rejected"
        row["exception"] = {"type": type(exc).__name__, "message": str(exc),
                            "incompatible_axes": getattr(exc, "incompatible_axes", None)}
        if expect != "reject" or not isinstance(exc, (ValueError, TypeError, KeyError)):
            row["findings"].append("unexpected rejection or exception type")
        return row
    finally:
        set_ctx_observer(None)
    row["disposition"] = "accepted"
    row["input"] = grid
    if expect == "reject":
        row["findings"].append("accepted a case expected to reject")
    row["input_sha256"] = hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()
    if not contexts:
        row["findings"].append("generate did not construct a GenCtx")
    else:
        ctx = contexts[-1]
        row["recorded_draws"] = ctx.recorded_draws()
        row["overrides_used"] = ctx.overrides_used()
        for axis in overrides:
            if axis not in row["overrides_used"]:
                row["findings"].append(f"accepted override {axis!r} was not consumed by GenCtx")
    try:
        realized = observe(module, grid)
        row["observed"] = realized
        for axis, requested in overrides.items():
            spec = getattr(module, "AXES", {}).get(axis, {})
            required = isinstance(spec, dict) and spec.get("type") in {"int", "color", "bool"}
            if required and axis not in realized:
                row["findings"].append(f"exact axis {axis!r} has no observable value")
            elif axis in realized and realized[axis] != requested:
                row["findings"].append(f"{axis}: requested {requested!r}, observed {realized[axis]!r}")
        for axis, drawn in row.get("recorded_draws", {}).items():
            if axis in realized and drawn != realized[axis]:
                row["findings"].append(f"{axis}: keyed draw {drawn!r}, observed {realized[axis]!r}")
    except Exception as exc:
        row["findings"].append(f"observation failed: {type(exc).__name__}: {exc}")
    validator = getattr(module, "self_check", None)
    if callable(validator):
        try:
            errors = invoke_validator(validator, grid, band, overrides)
            row["self_check"] = errors
            if not isinstance(errors, list) or errors:
                row["findings"].append("accepted input failed self_check list[str] contract or validation")
        except Exception as exc:
            row["findings"].append(f"self_check raised {type(exc).__name__}: {exc}")
    else:
        row["findings"].append("self_check is absent")
    try:
        if module.generate(seed, index, difficulty=band, **overrides) != grid:
            row["findings"].append("deterministic replay differs")
    except Exception as exc:
        row["findings"].append(f"replay raised {type(exc).__name__}: {exc}")
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[2] / "generator.py")
    parser.add_argument("--case", action="append", default=[], help="JSON override dict; expected acceptance")
    parser.add_argument("--reject-case", action="append", default=[], help="JSON override dict; expected rejection")
    parser.add_argument("--bands", default="easy,medium,hard")
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--sample-index", type=int, default=3)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("--out must be a new path; preserve previous results")
    source = args.source.resolve()
    source_bytes = source.read_bytes()
    module = types.ModuleType("task_control_probe_target")
    module.__file__ = str(source)
    sys.modules[module.__name__] = module
    # Compile the exact bytes hashed below, so a concurrent source edit cannot
    # make the report claim a different version from the one actually loaded.
    exec(compile(source_bytes, str(source), "exec"), module.__dict__)
    cases = [({}, "accept")]
    cases += [(json.loads(value), "accept") for value in args.case]
    cases += [(json.loads(value), "reject") for value in args.reject_case]
    cases += [({"__override_contract_unknown_axis__": 123}, "reject")]
    if any(not isinstance(case, dict) for case, _ in cases):
        parser.error("every case must be a JSON object of override names and values")
    rows = [probe_draw(module, band, args.seed, args.sample_index, case, expect)
            for band in args.bands.split(",") for case, expect in cases]
    malformed = []
    validator = getattr(module, "self_check", None)
    if callable(validator):
        for name, grid in (("empty", []), ("empty_row", [[]]), ("ragged", [[0, 0], [0]]),
                           ("invalid_color", [[10]]), ("boolean_cell", [[True]])):
            item = {"name": name, "input": grid, "findings": []}
            try:
                errors = invoke_validator(validator, grid, "medium", {})
                item["self_check"] = errors
                if not isinstance(errors, list) or not errors:
                    item["findings"].append("malformed grid not rejected with a nonempty reason list")
            except Exception as exc:
                item["findings"].append(f"validator raised {type(exc).__name__}: {exc}")
            malformed.append(item)
    findings = sum(len(row["findings"]) for row in rows + malformed)
    report = {"task_id": getattr(module, "TASK_ID", None), "generator_source": str(source),
              "generator_sha256": hashlib.sha256(source_bytes).hexdigest(),
              "generator_version": getattr(module, "VERSION", None),
              "command": [sys.executable, *sys.argv], "cwd": str(Path.cwd()),
              "declarations": {name: describe(getattr(module, name)) for name in DECLARATIONS if hasattr(module, name)},
              "hooks": {name: describe(getattr(module, name)) for name in HOOKS if hasattr(module, name)},
              "scope": "Explicit cases and five malformed inputs; no reference labels, domain inference, or lesson claim.",
              "draws": rows, "malformed_validation": malformed,
              "summary": {"draw_count": len(rows), "finding_count": findings,
                          "status": "pass" if not findings else "findings"}}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, default=repr) + "\n")
    print(json.dumps({"report": str(args.out), "generator_sha256": report["generator_sha256"], **report["summary"]}))
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
