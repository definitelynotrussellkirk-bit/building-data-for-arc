#!/usr/bin/env python3
"""Finite, source-bound canonical/lesson/control audit for 02280b74c8ab.

From the packet root (the wrapper's effective cwd is repo):
  python3 run_with_racket.py python3 generators/02280b74c8ab/workspace/probe_mosaic.py \
      --out ../checks/mosaic-probe.json --seed-count 20 --joint-controls

Each seed/band generates period + EXAMPLES_NEEDED consecutive inputs, covering
every cyclic start of SCHEDULE_PROFILES with four demonstrations plus one query.
Every pair is held out once. For a five-profile schedule this is nine inputs,
five windows and 25 query rotations per seed/band.
These overlapping windows are a task-local schedule audit, not independent
production-sampler lessons. All authoritative outputs come from Catalog.apply
in batches of at most 64. No Python reference clone or solve files are used.
The report retains exact grids, source hashes, requests, rotations and failures.
An agreeing rival is not ambiguity; a rival must fit all demonstrations and
disagree on the query. This finite declared-rival audit makes no universal
identifiability claim. --out must be a new file; partial/error reports never pass.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import importlib
import importlib.util
import itertools
import json
import math
from pathlib import Path
import sys
import time
from typing import Any

TASK_ID = "02280b74c8ab"
BANDS = (None, "easy", "medium", "hard")
BOUNDARIES = {"grid_h": (10, 20), "grid_w": (12, 22), "tpl_size": (2, 3),
              "code_shape": ("2x3", "3x2", "2x4", "3x3", "gapped"),
              "decor_9": (0, 1)}


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, separators=(",", ":"),
                                     sort_keys=True).encode()).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def positive_int(text: str) -> int:
    value = int(text)
    if value < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return value


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    result.add_argument("--out", type=Path, required=True, help="new JSON report path")
    result.add_argument("--seed-count", type=positive_int, default=20)
    result.add_argument("--seed-start", type=int, default=0)
    result.add_argument("--joint-controls", action="store_true",
                        help="include the complete 80-case boundary product per band/start")
    result.add_argument("--timeout", type=float, default=120,
                        help="seconds per public Catalog.apply batch")
    return result


def load_task():
    """Bind imports to this file's own library or copied task-test runtime."""
    here = Path(__file__).resolve()
    for candidate in here.parents:
        helper = next((p for p in (candidate / "reviewer_support.py",
                                   candidate / "shared/runtime/reviewer_support.py")
                       if p.is_file()), None)
        if helper is not None:
            sys.path.insert(0, str(helper.parent))
            break
    else:
        raise FileNotFoundError("No local reviewer_support.py above this probe")
    from reviewer_support import canonical_pairs, find_root, normalize_grid

    root = find_root(here)
    for path in (root, root / "shared/runtime", root / "src"):
        if path.is_dir() and str(path) not in sys.path:
            sys.path.insert(0, str(path))
    selected = root / "generators" / TASK_ID / "generator.py"
    name = f"generators.{TASK_ID}.generator"
    if not selected.is_file():
        selected = root / "puzzle_generators/per_puzzle" / TASK_ID / "generator.py"
        name = f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
    # Keep the supported module/package path while compiling these exact bytes,
    # so a same-size edit in one timestamp tick cannot reuse stale bytecode.
    importlib.import_module(name.rsplit(".", 1)[0])
    raw = selected.read_bytes()
    spec = importlib.util.spec_from_file_location(name, selected)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(raw, str(selected), "exec"), module.__dict__)
    source_hash = hashlib.sha256(raw).hexdigest()
    if file_hash(selected) != source_hash:
        raise RuntimeError("Generator source changed while importing")
    from arcpuzzles import Catalog

    catalog = Catalog(root)
    return root, module, catalog, canonical_pairs(TASK_ID, root=root), normalize_grid, source_hash


def declared_rivals(module):
    declarations, rivals = {}, {}
    for key in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS", "SEMANTIC_RIVALS"):
        value = getattr(module, key, None)
        if not isinstance(value, dict) or not value:
            raise ValueError(f"{key} must be a nonempty name-to-callable mapping")
        for name, function in value.items():
            if not isinstance(name, str) or not name or not callable(function):
                raise ValueError(f"Invalid {key} declaration: {name!r}")
            if name in rivals and rivals[name] is not function:
                raise ValueError(f"Conflicting rival functions named {name!r}")
            rivals[name] = function
        declarations[key] = list(value)
    return declarations, rivals


def incompatibility(module, requested, exception) -> dict | None:
    """Accept structured, declared refusals; a bare ValueError is an error."""
    if not isinstance(exception, ValueError) or len(requested) < 2:
        return None
    for attribute in ("incompatible_axes", "axes", "override_axes"):
        axes = getattr(exception, attribute, None)
        if isinstance(axes, (tuple, list, set)) and len(axes) >= 2 and set(axes) <= set(requested):
            return {"exception_attribute": attribute, "axes": sorted(axes)}
    for entry in getattr(module, "INCOMPATIBLE_OVERRIDE_COMBINATIONS", ()):
        if isinstance(entry, dict):
            matched = len(entry) >= 2 and all(
                key in requested and (value is None or requested[key] == value)
                for key, value in entry.items())
        else:
            matched = (isinstance(entry, (tuple, list)) and len(entry) >= 2
                       and set(entry) <= set(requested))
        if matched:
            return {"declaration": entry}
    return None


def control_cases(module, joint: bool):
    cases = [("single_axis", {axis: value}) for axis, values in BOUNDARIES.items()
             for value in values]
    if joint:
        cases.extend(("joint_boundary", dict(zip(BOUNDARIES, values)))
                     for values in itertools.product(*BOUNDARIES.values()))
    textures = tuple(dict.fromkeys((*getattr(module, "HELPFUL_TEXTURES", ()),
                                   *getattr(module, "DEGENERATE_TEXTURES", ()))))
    if not textures:
        raise ValueError("No texture declarations available for control audit")
    cases.extend(("shape_texture", {"code_shape": shape, "texture": texture})
                 for shape in BOUNDARIES["code_shape"] for texture in textures)
    return cases


class Audit:
    def __init__(self, args, report, checkpoint):
        self.args, self.report, self.checkpoint = args, report, checkpoint
        self.root, self.gen, self.catalog, self.canonical, self.normalize, imported_hash = load_task()
        self.declarations, self.rivals = declared_rivals(self.gen)
        self.predictions = {}
        self.generator_path = Path(self.gen.__file__).resolve()
        self.generator_hash = file_hash(self.generator_path)
        if self.generator_hash != imported_hash:
            raise RuntimeError("Generator source changed after import")
        described = self.catalog.describe(TASK_ID)
        if described["generator_sha256"] != self.generator_hash:
            raise RuntimeError("Catalog and imported generator hashes differ")
        declared_rule = getattr(self.gen, "RULE_HASH", None)
        if declared_rule is not None and declared_rule != described["rule_hash"]:
            raise RuntimeError("Declared RULE_HASH differs from the selected canonical authority")
        examples = getattr(self.gen, "EXAMPLES_NEEDED", None)
        if examples != 4:
            raise ValueError(f"This audit requires EXAMPLES_NEEDED=4; got {examples!r}")
        profiles = getattr(self.gen, "SCHEDULE_PROFILES", None)
        if not isinstance(profiles, (tuple, list)) or not profiles:
            raise ValueError("SCHEDULE_PROFILES must be a nonempty sequence")
        self.profiles = list(profiles)
        self.period = len(profiles)
        self.window_size = examples + 1
        self.report.update(
            sources={"generator_path": str(self.generator_path),
                     "generator_sha256": self.generator_hash,
                     "generator_version": getattr(self.gen, "VERSION", None),
                     "declared_rule_hash": getattr(self.gen, "RULE_HASH", None),
                     "catalog_rule_hash": described["rule_hash"], "root": str(self.root)},
            contract={"examples_needed": examples, "query_count": 1,
                      "schedule_period": self.period, "schedule_profiles": self.profiles,
                      "schedule_profiles_declared": hasattr(self.gen, "SCHEDULE_PROFILES"),
                      "inputs_per_seed_band": self.period + self.window_size - 1,
                      "declarations": self.declarations, "rival_count": len(self.rivals)},
            inputs={}, canonical=[], samples=[], lessons=[], racket_batches=[],
            counterexamples=[], failures=[], limits=[
                "Finite declared-rival evidence; no universal identifiability claim.",
                "Task-local consecutive windows; not the production lesson materializer.",
                "Cyclic starts and leave-one-out rotations overlap; counts are not independent draws.",
                "Rival scope is CANONICAL_SHORTCUTS, LESSON_COMPETITORS and SEMANTIC_RIVALS; predictions are cached by rival/input hash and assume pure deterministic callables.",
                "Control overrides can disable helpful teaching profiles; controls are validated and labelled, not treated as ordinary lessons.",
            ])

    def fail(self, kind, **details):
        self.report["failures"].append({"kind": kind, **details})

    def register(self, grid):
        grid = self.normalize(grid)
        key = digest(grid)
        self.report["inputs"].setdefault(key, {"input": grid})
        return key

    def observe(self, record, grid, band, requested):
        try:
            errors = self.gen.self_check(copy.deepcopy(grid), difficulty=band, meta=requested)
            if not isinstance(errors, list):
                raise TypeError("self_check must return a list")
            record["validator_errors"] = errors
            if errors:
                self.fail("validator_rejection", record=record["id"], errors=errors)
        except Exception as exc:
            record["validator_error"] = f"{type(exc).__name__}: {exc}"
            self.fail("validator_error", record=record["id"], error=record["validator_error"])
        try:
            observed = self.gen.observe_overrides(copy.deepcopy(grid))
            if not isinstance(observed, dict):
                raise TypeError("observe_overrides must return a dict")
            record["observed"] = observed
            pixels = {"grid_h": len(grid), "grid_w": len(grid[0]),
                      "decor_9": int(any(9 in row for row in grid))}
            if any(axis in observed and observed[axis] != value for axis, value in pixels.items()):
                self.fail("observer_pixel_mismatch", record=record["id"], pixels=pixels, observed=observed)
            missing = [axis for axis in requested if axis not in observed]
            mismatched = {axis: {"requested": value, "observed": observed.get(axis)}
                          for axis, value in requested.items() if observed.get(axis) != value}
            if missing or mismatched:
                self.fail("override_observation_mismatch", record=record["id"],
                          missing=missing, mismatched=mismatched)
        except Exception as exc:
            record["observer_error"] = f"{type(exc).__name__}: {exc}"
            self.fail("observer_error", record=record["id"], error=record["observer_error"])

    def draw(self, *, kind, band, seed, sample_index, requested=None, case_kind=None):
        requested = dict(requested or {})
        record = {"id": f"sample-{len(self.report['samples'])}", "kind": kind,
                  "difficulty": band, "seed": seed, "sample_index": sample_index,
                  "requested": requested}
        if case_kind:
            record["case_kind"] = case_kind
        self.report["samples"].append(record)
        try:
            grid = self.gen.generate(seed, sample_index, difficulty=band, **requested)
        except Exception as exc:
            record["generation_error"] = f"{type(exc).__name__}: {exc}"
            refusal = incompatibility(self.gen, requested, exc)
            if refusal is not None:
                record.update(generation_status="declared_incompatible", incompatibility=refusal)
            else:
                record["generation_status"] = "error"
                self.fail("generation_error", record=record["id"], error=record["generation_error"])
            return record
        record["generation_status"] = "generated"
        try:
            record["input_sha256"] = self.register(grid)
        except Exception as exc:
            record["grid_error"] = f"{type(exc).__name__}: {exc}"
            self.fail("generated_grid_error", record=record["id"], error=record["grid_error"])
            return record
        self.observe(record, grid, band, requested)
        if hasattr(self.gen, "schedule_profile"):
            try:
                record["schedule_profile"] = self.gen.schedule_profile(seed, sample_index, difficulty=band)
            except Exception as exc:
                record["schedule_profile_error"] = f"{type(exc).__name__}: {exc}"
                self.fail("schedule_profile_error", record=record["id"], error=record["schedule_profile_error"])
        return record

    def label_pending(self):
        pending = [key for key, value in self.report["inputs"].items() if "racket" not in value]
        for offset in range(0, len(pending), 64):
            keys = pending[offset:offset + 64]
            if file_hash(self.generator_path) != self.generator_hash:
                raise RuntimeError("Generator changed during the audit; use a new output path")
            applied = self.catalog.apply(TASK_ID, [self.report["inputs"][key]["input"] for key in keys],
                                         reference="canonical", timeout=self.args.timeout)
            batch = {key: value for key, value in applied.items() if key != "results"}
            batch.update(batch_index=len(self.report["racket_batches"]), input_hashes=keys,
                         input_count=len(keys))
            self.report["racket_batches"].append(batch)
            if (applied["generator_sha256"] != self.generator_hash
                    or not applied["rule_hash_matches_catalog"]
                    or applied["executed_rule_hash"] != self.report["sources"]["catalog_rule_hash"]):
                raise RuntimeError("Reference batch source identity does not match the audit")
            rule_text_hash = self.report["sources"].setdefault("executed_rule_text_sha256", applied["rule_text_sha256"])
            if rule_text_hash != applied["rule_text_sha256"]:
                raise RuntimeError("Executed Racket source changed between reference batches")
            for key, result in zip(keys, applied["results"], strict=True):
                if key != result["input_sha256"]:
                    raise RuntimeError("Reference returned a different input identity")
                self.report["inputs"][key]["racket"] = {
                    field: value for field, value in result.items() if field not in {"input", "index"}}
                if result.get("error") or not result.get("valid_output"):
                    self.fail("reference_error", input_sha256=key, error=result.get("error"))
            self.checkpoint()

    def score_input(self, key):
        if key in self.predictions:
            return self.predictions[key]
        item = self.report["inputs"][key]
        result = {}
        for name, function in self.rivals.items():
            try:
                prediction = self.normalize(function(copy.deepcopy(item["input"])))
                status = ("agrees" if prediction == item["racket"]["output"] else "differs")
                result[name] = {"status": status, "output": prediction,
                                "output_sha256": digest(prediction)}
            except Exception as exc:
                result[name] = {"status": "error", "error": f"{type(exc).__name__}: {exc}"}
                self.fail("rival_error", rival=name, input_sha256=key, error=result[name]["error"])
        item["rivals"] = {name: {field: value for field, value in score.items() if field != "output"}
                          for name, score in result.items()}
        self.predictions[key] = result
        return result

    def canonical_audit(self):
        for pair in self.canonical:
            record = {key: pair[key] for key in ("variant", "split", "pair_index")}
            record.update(id=f"canonical-{len(self.report['canonical'])}",
                          input_sha256=self.register(pair["input"]),
                          recorded_output=pair["output"], recorded_output_sha256=digest(pair["output"]))
            self.observe(record, pair["input"], None, {})
            self.report["canonical"].append(record)
        self.label_pending()
        fits = {name: Counter() for name in self.rivals}
        for record in self.report["canonical"]:
            key = record["input_sha256"]
            item = self.report["inputs"][key]
            if item["racket"]["output"] is None:
                record["usable"] = False
                continue
            record["usable"] = True
            if item["racket"]["output"] != record["recorded_output"]:
                self.fail("canonical_authority_mismatch", record=record["id"])
            for name, score in self.score_input(key).items():
                fits[name][score["status"]] += 1
        usable = sum(record.get("usable", False) for record in self.report["canonical"])
        self.report["canonical_rival_fit"] = {
            name: {"usable_pairs": usable, "counts": dict(counts),
                   "fits_every_usable_pair": usable > 0 and counts["agrees"] == usable}
            for name, counts in fits.items()}
        for name in self.declarations["CANONICAL_SHORTCUTS"]:
            if not self.report["canonical_rival_fit"][name]["fits_every_usable_pair"]:
                self.fail("claimed_canonical_shortcut_does_not_fit", rival=name)
        self.checkpoint()

    def lessons_audit(self):
        for band in BANDS:
            for seed in range(self.args.seed_start, self.args.seed_start + self.args.seed_count):
                records = [self.draw(kind="lesson", band=band, seed=seed, sample_index=index)
                           for index in range(self.period + self.window_size - 1)]
                for start in range(self.period):
                    self.report["lessons"].append({
                        "id": f"lesson-{len(self.report['lessons'])}", "difficulty": band,
                        "seed": seed, "cyclic_start": start,
                        "sample_ids": [record["id"] for record in records[start:start + self.window_size]]})
        self.label_pending()
        samples = {record["id"]: record for record in self.report["samples"]}
        for lesson in self.report["lessons"]:
            records = [samples[key] for key in lesson["sample_ids"]]
            if any("input_sha256" not in record or self.report["inputs"][record["input_sha256"]]["racket"]["output"] is None
                   for record in records):
                lesson["status"] = "incomplete"
                self.fail("incomplete_lesson", lesson=lesson["id"])
                continue
            scores = [self.score_input(record["input_sha256"]) for record in records]
            lesson["rotations"] = []
            for query_index in range(self.window_size):
                demos = [index for index in range(self.window_size) if index != query_index]
                rotation = {"query_index": query_index, "demo_indices": demos, "rivals": {}}
                for name in self.rivals:
                    statuses = [scores[index][name]["status"] for index in range(self.window_size)]
                    if "error" in statuses:
                        status = "error"
                    elif any(statuses[index] == "differs" for index in demos):
                        status = "refuted_by_demos"
                    elif statuses[query_index] == "agrees":
                        status = "survived_all"
                    else:
                        status = "ambiguous"
                        # Exact grids/authoritative labels are retained in inputs,
                        # keyed by each referenced sample's input_sha256.
                        counterexample = {"lesson_id": lesson["id"], "rival": name,
                                          "demo_sample_ids": [records[index]["id"] for index in demos],
                                          "query_sample_id": records[query_index]["id"],
                                          "query_index": query_index,
                                          "rival_query_output": scores[query_index][name]["output"]}
                        self.report["counterexamples"].append(counterexample)
                        self.fail("ambiguous_query", lesson=lesson["id"], query_index=query_index, rival=name)
                    rotation["rivals"][name] = status
                lesson["rotations"].append(rotation)
            lesson["status"] = "scored"
        self.checkpoint()

    def controls_audit(self):
        cases = control_cases(self.gen, self.args.joint_controls)
        for band in BANDS:
            for start in range(self.period):
                for case_index, (kind, requested) in enumerate(cases):
                    self.draw(kind="override", band=band, seed=self.args.seed_start + case_index,
                              sample_index=start, requested=requested, case_kind=kind)
        self.label_pending()

    def finish(self):
        if file_hash(self.generator_path) != self.generator_hash:
            raise RuntimeError("Generator changed during audit")
        samples = self.report["samples"]
        bands = {}
        for band in BANDS:
            draws = [row for row in samples if row["kind"] == "lesson" and row["difficulty"] == band]
            lessons = [row for row in self.report["lessons"] if row["difficulty"] == band]
            statuses = Counter(value for lesson in lessons for rotation in lesson.get("rotations", ())
                               for value in rotation["rivals"].values())
            bands[band or "default"] = {"sample_requests": len(draws),
                "successful_generations": sum(row["generation_status"] == "generated" for row in draws),
                "unique_inputs": len({row["input_sha256"] for row in draws if "input_sha256" in row}),
                "windows": len(lessons), "query_rotations": sum(len(row.get("rotations", ())) for row in lessons),
                "rival_decisions": dict(statuses)}
        controls = [row for row in samples if row["kind"] == "override"]
        lesson_draws = [row for row in samples if row["kind"] == "lesson"]
        self.report["totals"] = {
            "canonical_pairs": len(self.canonical),
            "canonical_usable_pairs": sum(row.get("usable", False) for row in self.report["canonical"]),
            "canonical_validator_accepted": sum(row.get("validator_errors") == [] for row in self.report["canonical"]),
            "sample_requests": len(samples), "unique_inputs": len(self.report["inputs"]),
            "lesson_sample_requests": len(lesson_draws),
            "lesson_unique_inputs": len({row["input_sha256"] for row in lesson_draws if "input_sha256" in row}),
            "lesson_windows": len(self.report["lessons"]),
            "query_rotations": sum(len(row.get("rotations", ())) for row in self.report["lessons"]),
            "reference_inputs": sum(len(row["input_hashes"]) for row in self.report["racket_batches"]),
            "racket_batches": len(self.report["racket_batches"]), "per_band": bands,
            "override_requests": len(controls),
            "override_unique_inputs": len({row["input_sha256"] for row in controls if "input_sha256" in row}),
            "override_case_kinds": dict(Counter(row["case_kind"] for row in controls)),
            "override_classifications": dict(Counter(row["generation_status"] for row in controls)),
            "override_validator_accepted": sum(row.get("validator_errors") == [] for row in controls),
            "counterexamples": len(self.report["counterexamples"]), "failures": len(self.report["failures"])}
        self.report["status"] = "pass" if not self.report["failures"] else "fail"


def main(argv=None) -> int:
    ap = parser()
    args = ap.parse_args(argv)
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        ap.error("--timeout must be finite and positive")
    out = args.out.resolve()
    if out.exists():
        ap.error(f"--out must be new; refusing to replace {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    report = {"schema": "02280b74c8ab-mosaic-audit-v1", "task_id": TASK_ID,
              "status": "running", "invocation": {"argv": list(sys.orig_argv),
                  "cwd": str(Path.cwd().resolve()), "executable": sys.executable,
                  "programmatic_argv": argv},
              "probe_sha256": file_hash(Path(__file__)),
              "options": {**vars(args), "out": str(out)}}
    with out.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, separators=(",", ":"))

    def checkpoint():
        temporary = out.with_name(out.name + ".partial")
        temporary.write_text(json.dumps(report, separators=(",", ":")) + "\n", encoding="utf-8")
        temporary.replace(out)

    started = time.monotonic()
    try:
        audit = Audit(args, report, checkpoint)
        audit.canonical_audit()
        audit.lessons_audit()
        audit.controls_audit()
        audit.finish()
    except Exception as exc:
        report["status"] = "error"
        report["error"] = f"{type(exc).__name__}: {exc}"
        if hasattr(exc, "run"):
            report["failed_reference_process"] = exc.run
    report["elapsed_seconds"] = round(time.monotonic() - started, 3)
    checkpoint()
    print(json.dumps({key: report[key] for key in ("status", "totals", "error") if key in report}, indent=2))
    return {"pass": 0, "fail": 1}.get(report["status"], 2)


if __name__ == "__main__":
    raise SystemExit(main())
