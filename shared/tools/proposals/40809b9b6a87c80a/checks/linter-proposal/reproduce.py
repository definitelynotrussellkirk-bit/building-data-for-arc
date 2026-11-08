#!/usr/bin/env python3
"""Reproduce linter sampling aliasing without importing private scripts.* APIs.

Run through review.py run. This executes the sampling prefix of the actual
original/candidate lint_one AST and the unmodified axis-honesty probe. It does
not pretend to run the remaining linter detectors. --racket separately obtains
authoritative outputs through Catalog.apply for the structural diagnostic.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import types

from reviewer_support import canonical_path, find_root

TASK_ID = "2e663d812b7a"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
ORIGINAL = ROOT / "shared/tools/generator_defect_lint.py"
CANDIDATE = HERE / "candidate_generator_defect_lint.py"
FIXTURE = HERE / "baseline_generator.py"
BANDS = ["easy", "medium", "hard"]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def grid_hash(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def load_generator(path=FIXTURE):
    module = types.ModuleType("sampling_reproduction_generator")
    module.__file__ = str(path)
    exec(compile(Path(path).read_text(), str(path), "exec"), vars(module))
    return module


class CallSpy:
    def __init__(self, module):
        self.module = module
        self.calls = []

    def __getattr__(self, name):
        return getattr(self.module, name)

    def generate(self, seed, sample_index, *, difficulty=None):
        self.calls.append({"seed": seed, "sample_index": sample_index,
                           "difficulty": difficulty})
        return self.module.generate(seed, sample_index, difficulty=difficulty)


def probe_namespace(source_path, module):
    """Compile original definitions; stop lint_one immediately after sampling.

    The loop, generator call, exception return, observer registration and cleanup
    all come from the file being tested. Only the final return is supplied by
    this harness, so it can inspect captured population/provenance directly.
    """
    tree = ast.parse(Path(source_path).read_text(), filename=str(source_path))
    wanted = {"_is_grid", "_norm", "_parse_valid", "probe_axis_honesty",
              "_sample_requests", "_sampling_record", "_decode_grid", "_load_canon"}
    body = [deepcopy(node) for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in wanted]
    sampler = deepcopy(next(node for node in tree.body
                            if isinstance(node, ast.FunctionDef) and node.name == "lint_one"))
    boundary = next(i for i, node in enumerate(sampler.body)
                    if isinstance(node, ast.Assign)
                    and isinstance(node.value, ast.Call)
                    and isinstance(node.value.func, ast.Name)
                    and node.value.func.id == "_run_detectors")
    sampler.body = sampler.body[:boundary] + ast.parse(
        "return {'inputs': all_in, 'contexts': ctxs, "
        "'sampling': _sampling_record(m, sample_calls, seeds, bands) "
        "if 'sample_calls' in locals() else None}"
    ).body
    body.append(sampler)
    spy = CallSpy(module)
    namespace = {"re": re, "json": json, "Path": Path,
                 "_VALID_RANGE_RE": re.compile(r"^\s*(-?\d+)\s*\.\.\s*(-?\d+)\s*$"),
                 "CANON": canonical_path(ROOT),
                 "_load_gen": lambda task_id, gen_file: (spy, FIXTURE)}
    extracted = ast.fix_missing_locations(ast.Module(body=body, type_ignores=[]))
    exec(compile(extracted, str(source_path), "exec"), namespace)
    return namespace, spy


def sample_population(source_path, module, *, count=8, bands=BANDS):
    namespace, spy = probe_namespace(source_path, module)
    sampled = namespace["lint_one"](TASK_ID, rules={}, canon={}, bridge=None,
                                     seeds=count, bands=bands, fast=True)
    if "error" in sampled:
        return {"error": sampled, "requests": spy.calls}, namespace, []
    errors, warnings = namespace["probe_axis_honesty"](module, sampled["contexts"])
    inputs = sampled["inputs"]
    profiles = Counter(module.schedule_profile(row["seed"], row["sample_index"],
                                                row["difficulty"])
                       for row in spy.calls) if hasattr(module, "schedule_profile") else None
    observations = [module.observe_overrides(grid) for grid in inputs]
    observed = {key: sorted({row[key] for row in observations})
                for key in observations[0]} if observations else {}
    receipt = {"sample_count": len(inputs), "requests": spy.calls,
               "profile_counts": dict(profiles) if profiles is not None else None,
               "observed_axes": observed, "axis_errors": errors,
               "axis_warnings": warnings,
               "input_sha256s": [grid_hash(grid) for grid in inputs],
               "sampling": sampled["sampling"]}
    return receipt, namespace, inputs


def narrow_fixture():
    """A real provenance-generating control with truly untapped width support."""
    from puzzle_generators.base import gen_ctx
    module = types.SimpleNamespace(AXES={"grid_w": {"type": "int", "valid": "1..12"}})

    def generate(seed, sample_index, *, difficulty=None):
        ctx = gen_ctx(seed=seed, sample_index=sample_index, version="narrow-fixture-1",
                      task_id="sampling_narrow_fixture", difficulty=difficulty)
        width = ctx.draw_choice("grid_w", (6,))
        return [[1] * width]

    module.generate = generate
    module.observe_overrides = lambda grid: {"grid_w": len(grid[0])}
    return module


def verify_manifest():
    expected = json.loads((HERE / "manifest.json").read_text())
    for path, key in ((ORIGINAL, "shared_source_sha256"),
                      (CANDIDATE, "candidate_sha256"),
                      (FIXTURE, "baseline_generator_sha256")):
        if sha256(path) != expected[key]:
            raise ValueError(f"Source changed: {path}; this reproduction is hash-bound")
    return expected


def run(out, *, racket=False, generator_path=FIXTURE):
    expected = verify_manifest()
    generator_path = Path(generator_path).resolve()
    module = load_generator(generator_path)
    original, namespace, original_inputs = sample_population(ORIGINAL, module)
    candidate, _, candidate_inputs = sample_population(CANDIDATE, module)
    narrow, _, _ = sample_population(CANDIDATE, narrow_fixture())
    report = {"schema": "review-linter-sampling-proposal-v1",
              "scope": "Actual sampler-prefix and unchanged axis probe; remaining linter detectors are not executed.",
              "baseline_identity": expected,
              "generator_source": str(generator_path),
              "generator_sha256": sha256(generator_path),
              "original": original, "candidate": candidate, "narrow_control": narrow,
              "structural_diagnostic": {"status": "not_run"}}
    if racket:
        from arcpuzzles import Catalog
        from review_diagnostics import compare_structure, structural_signature
        unique_inputs = {grid_hash(grid): grid for grid in original_inputs + candidate_inputs}
        applied = Catalog(ROOT).apply(TASK_ID, list(unique_inputs.values()),
                                      timeout=180, check_generator_domain=True)
        for row in applied["results"]:
            if row.get("output") is None:
                raise RuntimeError(f"Racket failed: {row}")
        outputs = {grid_hash(row["input"]): row["output"] for row in applied["results"]}
        canonical = namespace["_load_canon"]()[TASK_ID]
        old_pairs = [{"input": grid, "output": outputs[grid_hash(grid)]}
                     for grid in original_inputs]
        new_pairs = [{"input": grid, "output": outputs[grid_hash(grid)]}
                     for grid in candidate_inputs]
        old_structure = compare_structure(canonical, old_pairs)
        new_structure = compare_structure(canonical, new_pairs)
        canonical_pairs = [{"input": pair[0], "output": pair[1]} for pair in canonical]
        witness = next((pair for pair in new_pairs
                        if structural_signature(pair)["persistent_markers"] in
                        {structural_signature(p)["persistent_markers"] for p in canonical_pairs}), None)
        report["structural_diagnostic"] = {
            "status": "measured_with_selected_Racket_rule",
            "canonical_scope": "Last canonical ledger record's train pairs, matching the actual stock _load_canon.",
            "canonical_pair_count": len(canonical),
            "unique_Racket_inputs": len(unique_inputs),
            "original": old_structure, "candidate": new_structure,
            "canonical_overlap_witness": witness,
            "label_receipt": str(out.with_name(out.stem + "-racket.json")),
            "input_producer_generator_sha256": sha256(generator_path),
            "label_snapshot_generator_sha256": applied["generator_sha256"],
            "rule_text_sha256": applied["rule_text_sha256"]}
        out.with_name(out.stem + "-racket.json").write_text(json.dumps(applied, indent=2) + "\n")
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"report": str(out), "generator_sha256": report["generator_sha256"],
                      "original_warnings": len(original["axis_warnings"]),
                      "candidate_warnings": len(candidate["axis_warnings"]),
                      "original_profiles": original["profile_counts"],
                      "candidate_profiles": candidate["profile_counts"],
                      "narrow_control_warnings": len(narrow["axis_warnings"]),
                      "structure": report["structural_diagnostic"]["status"]}, indent=2))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--generator", type=Path, default=FIXTURE)
    parser.add_argument("--racket", action="store_true")
    args = parser.parse_args()
    if args.out.exists():
        parser.error("Use a fresh --out path so earlier evidence is retained")
    run(args.out.resolve(), racket=args.racket, generator_path=args.generator)
