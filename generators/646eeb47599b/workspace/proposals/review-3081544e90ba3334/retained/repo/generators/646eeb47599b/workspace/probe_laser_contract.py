#!/usr/bin/env python3
"""Finite source-bound audit of this task's controls, rivals, and diagnostics.

Run from WORK through the wrapper; its payload cwd is WORK/repo::

    mkdir -p checks/laser-probe-tmp
    TMPDIR="$PWD/checks/laser-probe-tmp" python3 run_with_racket.py python3 \
      generators/646eeb47599b/workspace/probe_laser_contract.py \
      --out ../checks/laser-probe.json --per-band 32 --seed 0

The destination must be new. This script imports only the selected task,
portable reviewer_support helpers, and the public Catalog API. It independently
observes all 1,056 exact-control combinations at the chosen seed/index zero.
Unpinned diagnostic outputs are compared with canonical Racket execution in
batches of at most 64. Racket supplies labels; _laser_output is only a diagnostic.
Exit 0 means the finite checks passed, 1 means a contract failure, and 2 means
an infrastructure or source-binding error. No selected source is modified.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
from itertools import product
import json
import os
from pathlib import Path
import sys
import time


TASK = "646eeb47599b"
BANDS = ("easy", "medium", "hard")
NAMESPACES = ("SEMANTIC_RIVALS", "CANONICAL_SHORTCUTS", "LESSON_COMPETITORS")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def observe_pixels(grid):
    """Recover controls without calling the generator's observer or optics."""
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a nonempty sequence of rows")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("grid must contain nonempty rows")
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        raise ValueError("grid is ragged")
    if any(type(v) is not int or v not in (3, 7, 8) for row in grid for v in row):
        raise ValueError("cells must be literal integers in {3, 7, 8}")
    if {v for row in grid for v in row} != {3, 7, 8}:
        raise ValueError("the three task colors must all be present")
    seeds = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 3]
    if len(seeds) != 2 or sum(abs(seeds[0][a] - seeds[1][a]) for a in (0, 1)) != 1:
        raise ValueError("expected exactly two orthogonally adjacent green cells")
    return {"grid_h": h, "grid_w": w, "n_walls": sum(row.count(8) for row in grid),
            "orientation": "horizontal" if seeds[0][0] == seeds[1][0] else "vertical"}


class Probe:
    def __init__(self, args, handle):
        self.args, self.handle = args, handle
        self.started = time.monotonic()
        self.report = {
            "schema": "arcpuzzles-task-laser-contract-probe-v1", "task_id": TASK,
            "status": "running", "seed": args.seed, "per_band": args.per_band,
            "invocation": {"argv": [sys.executable, *sys.argv], "cwd": str(Path.cwd()),
                           "environment": {name: os.environ.get(name) for name in
                                           ("TMPDIR", "RACKET_PATH", "PYTHONPATH", "PYTHONDONTWRITEBYTECODE")}},
            "failures": [],
            "limits": [
                "Exactly one seed and sample_index zero for the full explicit-control matrix; other random support is unmeasured.",
                "Matrix cases receive independent pixel observation and self_check, not individual Racket labels.",
                "Unpinned samples use consecutive indices at one seed per band; they are direct draws, not production materializer lessons or rotations.",
                "Rival results concern only actual declared callables and the recorded canonical/reference inputs; they do not prove uniqueness.",
                "Canonical records may repeat the same pair across variants; unique counts are reported separately.",
                "A passing finite probe does not change approval or training admission.",
            ],
        }
        self.cache = {}
        self.checkpoint()

    def fail(self, kind, *, infrastructure=False, **detail):
        self.report["failures"].append({"kind": kind, "infrastructure": infrastructure, **detail})

    def checkpoint(self):
        self.report["elapsed_seconds"] = round(time.monotonic() - self.started, 3)
        self.handle.seek(0)
        json.dump(self.report, self.handle, sort_keys=True, separators=(",", ":"))
        self.handle.write("\n")
        self.handle.truncate()
        self.handle.flush()

    def predict(self, fn, grid):
        key = (id(fn), digest(grid))
        if key not in self.cache:
            copied = deepcopy(grid)
            try:
                value = fn(copied)
                if copied != grid:
                    raise ValueError("rival mutated its input")
                self.cache[key] = (value, None)
            except Exception as exc:
                self.cache[key] = (None, f"{type(exc).__name__}: {exc}")
        return self.cache[key]

    def initialize(self):
        from arcpuzzles import Catalog
        from reviewer_support import canonical_pairs, canonical_path, find_root

        self.root = find_root(__file__)
        self.source = self.root / "generators" / TASK / "generator.py"
        self.before_hash = file_hash(self.source)
        spec = importlib.util.spec_from_file_location("selected_laser_contract_generator", self.source)
        self.gen = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.gen)
        self.catalog = Catalog(self.root)
        metadata = self.catalog.get(TASK)
        self.rule_hash = metadata["rule_hash"]
        self.pairs = canonical_pairs(TASK, root=self.root, labeled_only=True)
        self.report["sources"] = {
            "generator_path": str(self.source), "generator_sha256": self.before_hash,
            "generator_version": getattr(self.gen, "VERSION", None), "catalog_rule_hash": self.rule_hash,
            "generator_declared_rule_hash": getattr(self.gen, "RULE_HASH", None),
            "probe_path": str(Path(__file__).resolve()), "probe_sha256": file_hash(Path(__file__)),
            "canonical_path": str(canonical_path(self.root)),
            "canonical_selected_pairs_sha256": digest(self.pairs),
        }
        if file_hash(self.source) != self.before_hash or metadata["generator_sha256"] != self.before_hash:
            self.fail("source_changed_during_import", infrastructure=True)
        if getattr(self.gen, "RULE_HASH", None) != self.rule_hash:
            self.fail("declared_rule_hash_mismatch", declared=getattr(self.gen, "RULE_HASH", None), actual=self.rule_hash)
        self.declarations = {}
        for namespace in NAMESPACES:
            declaration = getattr(self.gen, namespace, None)
            self.declarations[namespace] = {}
            if not isinstance(declaration, dict) or not declaration:
                self.fail("invalid_rival_declaration", namespace=namespace, detail="expected a nonempty name-to-callable mapping")
                continue
            for name, fn in declaration.items():
                if not isinstance(name, str) or not callable(fn):
                    self.fail("invalid_rival_entry", namespace=namespace, name=str(name), value_type=type(fn).__name__)
                else:
                    self.declarations[namespace][name] = fn
        self.report["declarations"] = {ns: sorted(entries) for ns, entries in self.declarations.items()}
        self.checkpoint()

    def canonical(self):
        rows = []
        for namespace, entries in self.declarations.items():
            for name, fn in entries.items():
                matched = 0
                errors = 0
                first_difference = None
                for pair in self.pairs:
                    prediction, error = self.predict(fn, pair["input"])
                    identity = {k: pair[k] for k in ("variant", "split", "pair_index")}
                    if error:
                        errors += 1
                        self.fail("canonical_rival_error", namespace=namespace, rival=name,
                                  canonical_pair=identity, input=pair["input"], error=error)
                    elif prediction == pair["output"]:
                        matched += 1
                    elif first_difference is None:
                        first_difference = {"canonical_pair": identity, "input_sha256": digest(pair["input"]),
                                            "expected_sha256": digest(pair["output"]), "prediction_sha256": digest(prediction)}
                status = "error" if errors else ("fits_all" if matched == len(self.pairs) else "refuted")
                rows.append({"namespace": namespace, "name": name, "status": status,
                             "matched_pairs": matched, "labeled_pairs": len(self.pairs),
                             "first_difference": first_difference})
                if namespace == "CANONICAL_SHORTCUTS" and status != "fits_all":
                    self.fail("canonical_shortcut_metadata_mismatch", rival=name, observed_status=status,
                              matched_pairs=matched, total_pairs=len(self.pairs), witness=first_difference)
        if not self.pairs:
            self.fail("empty_canonical_pair_set", infrastructure=True)
        diagnostic_matches = 0
        for pair in self.pairs:
            try:
                prediction = self.gen._laser_output(deepcopy(pair["input"]))
                if prediction == pair["output"]:
                    diagnostic_matches += 1
                else:
                    self.fail("canonical_diagnostic_mismatch", pair=pair, diagnostic_output=prediction)
            except Exception as exc:
                self.fail("canonical_diagnostic_error", pair=pair, error=f"{type(exc).__name__}: {exc}")
        self.report["canonical"] = {"labeled_pairs": len(self.pairs),
            "unique_inputs": len({digest(p["input"]) for p in self.pairs}),
            "unique_pairs": len({digest([p["input"], p["output"]]) for p in self.pairs}),
            "diagnostic_matches": diagnostic_matches, "rival_fit": rows}
        self.checkpoint()
        print(f"canonical: {len(self.pairs)} labeled records checked", file=sys.stderr, flush=True)

    def matrix(self):
        rows, unique = [], set()
        per_band = {band: {"attempted": 0, "passed": 0, "hashes": set()} for band in BANDS}
        for band, h, w, walls, orientation in product(BANDS, range(5, 9), range(5, 9), range(4, 15), ("horizontal", "vertical")):
            overrides = {"grid_h": h, "grid_w": w, "n_walls": walls, "orientation": orientation}
            context = {"seed": self.args.seed, "sample_index": 0, "difficulty": band, "overrides": overrides}
            start_failures = len(self.report["failures"])
            grid, input_hash = None, None
            per_band[band]["attempted"] += 1
            try:
                grid = self.gen.generate(self.args.seed, 0, difficulty=band, **overrides)
                input_hash = digest(grid)
                unique.add(input_hash)
                per_band[band]["hashes"].add(input_hash)
                observed = observe_pixels(grid)
                if observed != overrides or any(type(observed[k]) is not type(v) for k, v in overrides.items()):
                    self.fail("override_pixels_mismatch", **context, input=grid, observed=observed)
                declared = self.gen.observe_overrides(deepcopy(grid))
                if declared != observed or any(type(declared.get(k)) is not type(v) for k, v in observed.items()):
                    self.fail("override_observer_mismatch", **context, input=grid, independent=observed, declared=declared)
                errors = self.gen.self_check(deepcopy(grid), difficulty=band)
                if errors:
                    self.fail("override_self_check_failure", **context, input=grid, errors=errors)
            except Exception as exc:
                self.fail("override_case_error", **context, input=grid, error=f"{type(exc).__name__}: {exc}")
            passed = len(self.report["failures"]) == start_failures
            per_band[band]["passed"] += passed
            rows.append([band, h, w, walls, orientation, input_hash, passed])
        self.report["override_matrix"] = {"seed": self.args.seed, "sample_index": 0,
            "expected_cases": 1056, "attempted": len(rows), "passed": sum(row[-1] for row in rows),
            "unique_inputs": len(unique),
            "per_band": {band: {"attempted": r["attempted"], "passed": r["passed"], "unique_inputs": len(r["hashes"])} for band, r in per_band.items()},
            "case_columns": ["difficulty", "grid_h", "grid_w", "n_walls", "orientation", "input_sha256", "passed"],
            "cases": rows}
        self.checkpoint()
        print(f"override matrix: {len(rows)} cases, {sum(row[-1] for row in rows)} passed", file=sys.stderr, flush=True)

    def parity(self):
        samples = []
        for band in BANDS:
            for index in range(self.args.per_band):
                context = {"seed": self.args.seed, "sample_index": index, "difficulty": band, "overrides": {}}
                grid = None
                try:
                    grid = self.gen.generate(self.args.seed, index, difficulty=band)
                    observed = observe_pixels(grid)
                    errors = self.gen.self_check(deepcopy(grid), difficulty=band)
                    if errors:
                        self.fail("unpinned_self_check_failure", **context, input=grid, errors=errors)
                    diagnostic = self.gen._laser_output(deepcopy(grid))
                    profile_fn = getattr(self.gen, "schedule_profile", None)
                    profile = profile_fn(self.args.seed, index, band) if callable(profile_fn) else None
                    samples.append({**context, "input": grid, "input_sha256": digest(grid),
                                    "observed": observed, "schedule_profile": profile,
                                    "diagnostic_output": diagnostic, "diagnostic_sha256": digest(diagnostic)})
                except Exception as exc:
                    self.fail("unpinned_generation_error", **context, input=grid, error=f"{type(exc).__name__}: {exc}")
        batches = []
        self.report["racket_parity"] = {"expected_samples": 3 * self.args.per_band,
            "generated_samples": len(samples), "samples": samples, "batches": batches}
        self.checkpoint()
        for start in range(0, len(samples), 64):
            batch = samples[start:start + 64]
            try:
                result = self.catalog.apply(TASK, [p["input"] for p in batch], timeout=120)
                binding_keys = ("schema", "reference", "executed_rule_hash", "catalog_rule_hash", "rule_text_sha256", "generator_sha256", "rule_hash_matches_catalog", "elapsed_seconds")
                binding = {k: result.get(k) for k in binding_keys}
                batches.append({"first_sample": start, "count": len(batch), "api": "Catalog.apply", "timeout": 120, **binding})
                if result.get("generator_sha256") != self.before_hash or result.get("executed_rule_hash") != self.rule_hash or not result.get("rule_hash_matches_catalog"):
                    self.fail("reference_source_binding_mismatch", infrastructure=True, first_sample=start, observed=binding)
                outcomes = result.get("results", [])
                if len(outcomes) != len(batch):
                    self.fail("reference_result_count_mismatch", infrastructure=True, first_sample=start, expected=len(batch), actual=len(outcomes))
                for offset, sample in enumerate(batch):
                    if offset >= len(outcomes):
                        continue
                    outcome = outcomes[offset]
                    context = {k: sample[k] for k in ("seed", "sample_index", "difficulty", "overrides")}
                    if outcome.get("index") != offset or outcome.get("input") != sample["input"]:
                        self.fail("reference_input_alignment_mismatch", infrastructure=True, **context, input=sample["input"], result=outcome)
                    if outcome.get("error") is not None or not outcome.get("valid_output"):
                        self.fail("reference_execution_failure", **context, input=sample["input"], result=outcome)
                        continue
                    output = outcome["output"]
                    sample["reference_output"] = output
                    sample["reference_sha256"] = digest(output)
                    sample["reference_tool_input_sha256"] = outcome.get("input_sha256")
                    sample["reference_tool_output_sha256"] = outcome.get("output_sha256")
                    sample["diagnostic_matches"] = sample["diagnostic_output"] == output
                    if not sample["diagnostic_matches"]:
                        self.fail("racket_diagnostic_mismatch", **context, input=sample["input"], reference_output=output, diagnostic_output=sample["diagnostic_output"])
                    else:
                        del sample["diagnostic_output"]
                    sample["rivals_matching_reference"] = {}
                    for namespace, entries in self.declarations.items():
                        matches = []
                        for name, fn in entries.items():
                            prediction, error = self.predict(fn, sample["input"])
                            if error:
                                self.fail("reference_rival_error", **context, namespace=namespace, rival=name, input=sample["input"], error=error)
                            elif prediction == output:
                                matches.append(name)
                                if namespace == "SEMANTIC_RIVALS" and sample["schedule_profile"] == "teaching":
                                    self.fail("teaching_draw_does_not_refute_declared_rival", **context, rival=name, input=sample["input"], reference_output=output)
                        sample["rivals_matching_reference"][namespace] = matches
            except Exception as exc:
                self.fail("reference_batch_error", infrastructure=True, first_sample=start,
                          sample_contexts=[{k: p[k] for k in ("seed", "sample_index", "difficulty", "overrides")} for p in batch],
                          error=f"{type(exc).__name__}: {exc}")
            self.checkpoint()
            print(f"Racket parity: batch {start // 64 + 1}, {len(batch)} inputs processed", file=sys.stderr, flush=True)
        self.report["racket_parity"].update(
            referenced_samples=sum("reference_output" in p for p in samples),
            diagnostic_matches=sum(p.get("diagnostic_matches", False) for p in samples),
            unique_inputs=len({p["input_sha256"] for p in samples}),
            per_band={band: {"generated": sum(p["difficulty"] == band for p in samples),
                            "referenced": sum(p["difficulty"] == band and "reference_output" in p for p in samples),
                            "diagnostic_matches": sum(p["difficulty"] == band and p.get("diagnostic_matches", False) for p in samples),
                            "unique_inputs": len({p["input_sha256"] for p in samples if p["difficulty"] == band}),
                            "profiles": dict(Counter(p["schedule_profile"] for p in samples if p["difficulty"] == band))} for band in BANDS})
        if sum("reference_output" in p for p in samples) != 3 * self.args.per_band:
            self.fail("incomplete_reference_population", expected=3 * self.args.per_band,
                      referenced=sum("reference_output" in p for p in samples))
        self.checkpoint()

    def finish(self):
        if hasattr(self, "source"):
            after = file_hash(self.source)
            self.report.setdefault("sources", {})["generator_sha256_after"] = after
            if after != self.before_hash:
                self.fail("source_changed_during_probe", infrastructure=True, expected=self.before_hash, actual=after)
        failures = self.report["failures"]
        code = 2 if any(f["infrastructure"] for f in failures) else (1 if failures else 0)
        self.report["status"] = "error" if code == 2 else ("failed" if code else "passed")
        self.report["failure_counts"] = dict(Counter(f["kind"] for f in failures))
        self.report["exit_code"] = code
        self.checkpoint()
        print(json.dumps({"status": self.report["status"], "failures": len(failures),
                          "output": str(self.args.out.resolve()), "exit_code": code}), flush=True)
        return code


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, required=True, help="new compact JSON receipt; refuses an existing path")
    parser.add_argument("--per-band", type=int, default=32, help="positive unpinned sample count in each difficulty (default: 32)")
    parser.add_argument("--seed", type=int, default=0, help="one reproducible sampler seed (default: 0)")
    args = parser.parse_args()
    if args.per_band <= 0:
        parser.error("--per-band must be positive")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    try:
        handle = args.out.open("x", encoding="utf-8")
    except FileExistsError:
        parser.error(f"output already exists: {args.out}")
    with handle:
        probe = Probe(args, handle)
        try:
            probe.initialize()
            probe.canonical()
            probe.matrix()
            probe.parity()
        except Exception as exc:
            probe.fail("probe_infrastructure_error", infrastructure=True, error=f"{type(exc).__name__}: {exc}")
        return probe.finish()


if __name__ == "__main__":
    raise SystemExit(main())
