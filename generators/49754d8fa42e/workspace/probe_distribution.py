#!/usr/bin/env python3
"""Source-bound distribution audit using only public Catalog reference execution.

The selected module supplies rival predictions; it never supplies correct labels.
Success rows retain hashes and replay tuples rather than repeated full grids.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import traceback

TASK_ID = "49754d8fa42e"
REGISTRIES = ("SEMANTIC_RIVALS", "CANONICAL_SHORTCUTS", "LESSON_COMPETITORS")
AXES = ("grid_h", "grid_w", "mode_color", "mode_count", "palette_size")


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":"), sort_keys=True).encode()).hexdigest()


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_grid(value):
    if isinstance(value, list) and value and all(isinstance(row, str) for row in value):
        value = [[int(cell) for cell in row] for row in value]
    if (not isinstance(value, list) or not 1 <= len(value) <= 30
            or any(not isinstance(row, list) or not 1 <= len(row) <= 30 for row in value)
            or any(len(row) != len(value[0]) for row in value)
            or any(type(cell) is not int or not 0 <= cell <= 9 for row in value for cell in row)):
        raise ValueError("expected rectangular 1..30 integer-color grid")
    return value


def axis_values(grid):
    """Descriptive observations only; this does not predict a reference answer."""
    counts = Counter(cell for row in grid for cell in row)
    foreground = Counter({color: count for color, count in counts.items() if color != 0})
    ranked = foreground.most_common()
    mode, mode_count = ranked[0] if ranked else (None, 0)
    if len(ranked) > 1 and ranked[1][1] == mode_count:
        mode = None  # Describe ambiguity instead of choosing a tied mode.
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "mode_color": mode,
            "mode_count": mode_count, "palette_size": len(counts)}


def load_generator(root):
    # Import the selected file and its supported generator helpers, not runner internals.
    sys.path.insert(0, str(root / "shared/runtime"))
    path = root / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location("distribution_probe_selected_generator", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    # Compile the hashed source bytes directly so a stale .pyc cannot supply code.
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module, path


class Audit:
    def __init__(self, options):
        self.options = options
        self.root = options.library.resolve()
        self.report = {"schema": "49754d8fa42e-distribution-probe-v1", "task_id": TASK_ID,
                       "started_utc": datetime.now(timezone.utc).isoformat(),
                       "parameters": {"count_per_band": options.count, "seed": options.seed,
                                      "window_seed_count": options.window_seeds,
                                      "window_start_count": options.window_starts,
                                      "bands": options.bands, "n_train": 5, "n_test": 2,
                                      "timeout_seconds": options.timeout},
                       "samplers": {
                           "catalog": "Catalog.generate increments seed per episode; all start at sample_index=0; accepted indices and rejections are retained.",
                           "windows": "All consecutive starts 0..window_starts-1 over one directly generated schedule per fixed seed; each window contains five demos and two queries. Reference labels use Catalog.apply batches of at most64. These windows overlap and are not independent inputs.",
                           "correct_labels": "Only authoritative canonical Racket outputs returned by public Catalog.generate or Catalog.apply; no intended Python solver.",
                           "axis_denominators": "Axis histograms count distinct input hashes within each sampler/band; occurrence counts and seed/sample tuples are separate."},
                       "registries": {}, "canonical": {}, "bands": {},
                       "reference_receipts": [], "errors": [], "failures": [], "failure_examples": {}}
        self.prediction_cache = {}
        self.module = None
        self.source = None
        self.source_start = None
        self.catalog = None
        self.registry_functions = {}

    def fail(self, category, detail, example=None):
        item = {"category": category, **detail}
        self.report["failures"].append(item)
        if example is not None:
            examples = self.report["failure_examples"].setdefault(category, [])
            if len(examples) < self.options.example_limit:
                examples.append({**item, "example": example})

    def error(self, category, exc, detail=None):
        item = {"category": category, **(detail or {}), "exception": type(exc).__name__,
                "message": str(exc), "traceback": traceback.format_exc()}
        run = getattr(exc, "run", None)
        if run is not None:
            item["process_receipt"] = run
        self.report["errors"].append(item)
        self.fail(category, {key: value for key, value in item.items() if key not in {"traceback", "process_receipt"}})

    def setup(self):
        from arcpuzzles import Catalog
        self.catalog = Catalog(self.root)
        before = self.root / "generators" / TASK_ID / "generator.py"
        self.source_start = file_hash(before)
        self.module, self.source = load_generator(self.root)
        if file_hash(self.source) != self.source_start:
            raise RuntimeError("selected generator changed while being imported")
        metadata = self.catalog.get(TASK_ID)
        self.report["source_identity"] = {
            "generator_relative_path": str(self.source.relative_to(self.root)),
            "generator_sha256_start": self.source_start,
            "probe_sha256": file_hash(Path(__file__).resolve()),
            "generator_version": getattr(self.module, "VERSION", None),
            "rule_hash": metadata["rule_hash"], "rule_task_id": metadata.get("rule_task_id"),
            "catalog_approved": metadata["approved"],
            "approval_reasons": metadata["approval_reasons"]}
        for group in REGISTRIES:
            registry = getattr(self.module, group, None)
            if not isinstance(registry, dict) or not registry:
                raise ValueError(f"{group} must be a nonempty dict[str, callable]")
            if any(not isinstance(name, str) or not callable(fn) for name, fn in registry.items()):
                raise ValueError(f"{group} must map string names to grid-prediction callables")
            self.registry_functions[group] = dict(registry)
            self.report["registries"][group] = list(registry)
        if getattr(self.module, "EXAMPLES_NEEDED", None) != 5:
            raise ValueError("this audit requires EXAMPLES_NEEDED=5")
        for hook in ("generate", "self_check", "schedule_profile", "lesson_identifiable"):
            if not callable(getattr(self.module, hook, None)):
                raise ValueError(f"missing supported generator hook {hook}")
        self.report["schedule_profiles"] = list(self.module.SCHEDULE_PROFILES)
        return metadata

    def predict(self, group, name, grid, expected):
        key = (group, name, digest(grid), digest(expected))
        if key not in self.prediction_cache:
            copied = deepcopy(grid)
            try:
                predicted = normalize_grid(self.registry_functions[group][name](copied))
                if copied != grid:
                    raise ValueError("rival predictor mutated its input")
                result = {"matches_reference": predicted == expected, "prediction_sha256": digest(predicted)}
            except Exception as exc:
                result = {"matches_reference": None, "error": type(exc).__name__ + ": " + str(exc)}
            self.prediction_cache[key] = result
        return self.prediction_cache[key]

    def canonical(self, metadata):
        usable, omitted = [], []
        for variant_index, variant in enumerate(metadata.get("variants", [])):
            for split in ("train", "test"):
                pairs = variant.get(split, [])
                if isinstance(pairs, dict):
                    pairs = [pairs]
                if not isinstance(pairs, list):
                    omitted.append({"variant": variant_index, "split": split, "reason": "pairs are not a list"})
                    continue
                for pair_index, pair in enumerate(pairs):
                    location = {"variant": variant_index, "split": split, "pair_index": pair_index}
                    try:
                        grid = normalize_grid(pair["input"])
                        expected = normalize_grid(pair["output"])
                    except (KeyError, TypeError, ValueError) as exc:
                        omitted.append({**location, "reason": str(exc)})
                        continue
                    usable.append((location, grid, expected))
        self.report["canonical"] = {"usable_pairs": len(usable), "omitted_pairs": omitted,
                                     "shortcut_results": {}, "pair_manifest": []}
        if not usable:
            self.fail("canonical_no_usable_pairs", {})
        for name in self.registry_functions["CANONICAL_SHORTCUTS"]:
            results = []
            for location, grid, expected in usable:
                result = self.predict("CANONICAL_SHORTCUTS", name, grid, expected)
                results.append({**location, **result})
                if result["matches_reference"] is not True:
                    self.fail("canonical_shortcut", {"shortcut": name, **location, **result},
                              {"input": grid, "reference_output": expected})
            self.report["canonical"]["shortcut_results"][name] = {
                "checked_pairs": len(results), "matched_pairs": sum(r["matches_reference"] is True for r in results),
                "fits_all_usable_pairs": bool(results) and all(r["matches_reference"] is True for r in results),
                "pairs": results}
        for location, grid, expected in usable:
            self.report["canonical"]["pair_manifest"].append(
                {**location, "input_sha256": digest(grid), "output_sha256": digest(expected)})

    def identity_check(self, generator_hash, rule_hash, location):
        if generator_hash != self.source_start or rule_hash != self.report["source_identity"]["rule_hash"]:
            self.fail("reference_source_identity", {**location, "generator_sha256": generator_hash,
                                                   "executed_rule_hash": rule_hash})

    def sample(self, grid, output, band, sampler, seed, sample_index):
        location = {"band": band, "sampler": sampler, "seed": seed, "sample_index": sample_index}
        grid, output = normalize_grid(grid), normalize_grid(output)
        copied = deepcopy(grid)
        reasons = list(self.module.self_check(copied, difficulty=band) or [])
        if copied != grid:
            reasons.append("self_check mutated input")
        if reasons:
            self.fail("input_self_check", {**location, "reasons": reasons}, {"input": grid, "reference_output": output})
        profile = self.module.schedule_profile(seed, sample_index, difficulty=band)
        if profile not in self.module.SCHEDULE_PROFILES:
            self.fail("unrecognized_schedule_profile", {**location, "profile": profile})
        if profile == "canonical_anchor" and callable(getattr(self.module, "strict_canonical_like", None)):
            anchor_reasons = list(self.module.strict_canonical_like(deepcopy(grid)) or [])
            if anchor_reasons:
                self.fail("canonical_anchor_validation", {**location, "reasons": anchor_reasons},
                          {"input": grid, "reference_output": output})
        return {**location, "input": grid, "output": output, "input_sha256": digest(grid),
                "output_sha256": digest(output), "axes": axis_values(grid), "schedule_profile": profile}

    def lesson(self, samples, location):
        if len(samples) != 7:
            self.fail("lesson_pair_count", {**location, "actual_pairs": len(samples)})
            return None
        demos, queries = samples[:5], samples[5:]
        pairs = [{"input": s["input"], "output": s["output"]} for s in demos]
        record = {**location, "sample_indices": [s["sample_index"] for s in samples],
                  "input_sha256": [s["input_sha256"] for s in samples],
                  "output_sha256": [s["output_sha256"] for s in samples],
                  "schedule_profiles": [s["schedule_profile"] for s in samples],
                  "demonstrated_mode_colors": sorted({s["axes"]["mode_color"] for s in demos}, key=lambda color: (color is None, color or 0)),
                  "rivals": {}, "identifiability_reasons": []}
        for query_index, query in enumerate(queries):
            reasons = list(self.module.lesson_identifiable(deepcopy(pairs), deepcopy(query["input"])) or [])
            record["identifiability_reasons"].append(reasons)
            if reasons:
                self.fail("lesson_identifiability", {**location, "query_index": query_index, "reasons": reasons},
                          {"demonstrations": pairs, "query": {"input": query["input"], "reference_output": query["output"]}})
        for group, registry in self.registry_functions.items():
            group_record = record["rivals"][group] = {}
            for name in registry:
                results = [self.predict(group, name, s["input"], s["output"]) for s in samples]
                refuted = any(r["matches_reference"] is False for r in results[:5])
                errors = [{"position": i, "sample_index": samples[i]["sample_index"], **r}
                          for i, r in enumerate(results) if r["matches_reference"] is None]
                survived = not refuted and not any(r["matches_reference"] is None for r in results[:5])
                outcome = {"refuted": refuted, "survived": survived,
                           "query_discriminates": [r["matches_reference"] is False for r in results[5:]],
                           "refuting_demo_indices": [i for i, r in enumerate(results[:5]) if r["matches_reference"] is False],
                           "errors": errors}
                group_record[name] = outcome
                if errors:
                    self.fail("rival_prediction_error", {**location, "registry": group, "rival": name, "errors": errors})
                if group == "LESSON_COMPETITORS" and survived:
                    self.fail("lesson_competitor_survived", {**location, "rival": name,
                                                            "query_discriminates": outcome["query_discriminates"]},
                              {"demonstrations": pairs, "queries": [{"input": s["input"], "reference_output": s["output"]} for s in queries]})
        return record

    def summarize(self, samples, lessons, requested):
        unique = {s["input_sha256"]: s for s in samples}
        tuples = {(s["seed"], s["sample_index"]) for s in samples}
        histogram = {axis: dict(sorted(Counter(str(s["axes"][axis]) for s in unique.values()).items())) for axis in AXES}
        rival_totals = {}
        for group, registry in self.registry_functions.items():
            rival_totals[group] = {}
            for name in registry:
                outcomes = [lesson["rivals"][group][name] for lesson in lessons]
                rival_totals[group][name] = {"denominator_lessons": len(outcomes),
                    "refuted": sum(r["refuted"] for r in outcomes), "survived": sum(r["survived"] for r in outcomes),
                    "query_discriminates": sum(any(r["query_discriminates"]) for r in outcomes),
                    "survived_and_query_discriminates": sum(r["survived"] and any(r["query_discriminates"]) for r in outcomes),
                    "prediction_error_lessons": sum(bool(r["errors"]) for r in outcomes)}
        return {"requested_lessons": requested, "completed_lessons": len(lessons),
                "pair_occurrences_in_lessons": len(samples), "unique_seed_sample_tuples": len(tuples),
                "unique_input_hashes": len(unique), "axis_unique_input_histograms": histogram,
                "schedule_profile_unique_input_histogram": dict(Counter(s["schedule_profile"] for s in unique.values())),
                "rival_totals": rival_totals, "lessons": lessons}

    def catalog_band(self, band):
        episodes = []
        try:
            episodes = self.catalog.generate(TASK_ID, count=self.options.count, seed=self.options.seed,
                difficulty=band, n_train=5, n_test=2, allow_unapproved=True, timeout=self.options.timeout)
        except Exception as exc:
            episodes = getattr(exc, "partial_episodes", [])
            self.error("catalog_generation", exc, {"band": band, "requested": self.options.count,
                                                   "completed": len(episodes)})
        self.report["reference_receipts"].append({"api": "Catalog.generate", "band": band,
            "arguments": {"task_id": TASK_ID, "count": self.options.count, "seed": self.options.seed,
                          "difficulty": band, "n_train": 5, "n_test": 2, "allow_unapproved": True,
                          "sample_index": 0, "reference": "canonical", "timeout": self.options.timeout},
            "completed_episodes": len(episodes)})
        samples, lessons = [], []
        for episode in episodes:
            location = {"band": band, "sampler": "catalog", "seed": episode["seed"],
                        "episode_index": episode.get("episode_index"), "start": episode.get("sample_index", 0)}
            try:
                self.identity_check(episode["provenance"]["generator_sha256"], episode["executed_rule_hash"], location)
                if len(episode["train"]) != 5 or len(episode["test"]) != 2:
                    raise ValueError("episode must have exactly five demonstrations and two queries")
                pairs = episode["train"] + episode["test"]
                indices = episode.get("sample_indices")
                if not isinstance(indices, list) or len(indices) != 7:
                    raise ValueError("public materializer did not return seven accepted sample indices")
                current = [self.sample(p["input"], p["output"], band, "catalog", episode["seed"], si)
                           for p, si in zip(pairs, indices, strict=True)]
                samples.extend(current)
                record = self.lesson(current, location)
                record["rejections"] = episode.get("rejections", [])
                record["executed_rule_hash"] = episode["executed_rule_hash"]
                record["program_text_sha256"] = hashlib.sha256(episode["program"].encode()).hexdigest()
                lessons.append(record)
                for rejection in record["rejections"]:
                    self.fail("catalog_rejected_sample", {**location, "rejection": rejection})
            except Exception as exc:
                self.error("catalog_episode_validation", exc, location)
        if len(lessons) != self.options.count:
            self.fail("catalog_lesson_denominator", {"band": band, "requested": self.options.count,
                                                     "completed": len(lessons)})
        return self.summarize(samples, lessons, self.options.count)

    def window_band(self, band):
        grids, tuples = [], []
        # Keep this seed family disjoint from the independent Catalog lessons.
        first_seed = self.options.seed + self.options.count + 10000
        length = self.options.window_starts + 6
        for seed in range(first_seed, first_seed + self.options.window_seeds):
            for si in range(length):
                try:
                    generated = self.module.generate(seed, si, difficulty=band)
                    grid = normalize_grid(generated.get("input") if isinstance(generated, dict) else generated)
                    grids.append(grid)
                    tuples.append((seed, si))
                except Exception as exc:
                    self.error("window_input_generation", exc, {"band": band, "seed": seed, "sample_index": si})
        reference_samples = {}
        for offset in range(0, len(grids), 64):
            inputs = grids[offset:offset + 64]
            batch_tuples = tuples[offset:offset + 64]
            receipt = {"api": "Catalog.apply", "band": band, "batch_offset": offset,
                       "arguments": {"task_id": TASK_ID, "reference": "canonical", "allow_unapproved": True,
                                     "timeout": self.options.timeout},
                       "seed_sample_tuples": [list(t) for t in batch_tuples],
                       "input_sha256": [digest(grid) for grid in inputs]}
            try:
                applied = self.catalog.apply(TASK_ID, inputs, allow_unapproved=True, timeout=self.options.timeout)
                self.identity_check(applied["generator_sha256"], applied["executed_rule_hash"], {"band": band, "batch_offset": offset})
                receipt.update({key: applied.get(key) for key in ("executed_rule_hash", "catalog_rule_hash",
                    "rule_text_sha256", "generator_sha256", "rule_file", "rule_task_id", "elapsed_seconds")})
                if len(applied["results"]) != len(inputs):
                    raise ValueError("reference returned an incomplete apply batch")
                receipt["output_sha256"] = []
                for item, (seed, si), grid in zip(applied["results"], batch_tuples, inputs, strict=True):
                    receipt["output_sha256"].append(item.get("output_sha256"))
                    try:
                        if item.get("output") is None or item.get("error"):
                            raise ValueError(f"reference execution failed: {item}")
                        reference_samples[(seed, si)] = self.sample(grid, item["output"], band, "windows", seed, si)
                    except Exception as exc:
                        self.error("window_reference_validation", exc, {"band": band, "seed": seed, "sample_index": si})
            except Exception as exc:
                self.error("window_reference_batch", exc, {"band": band, "batch_offset": offset,
                                                           "seed_sample_tuples": receipt["seed_sample_tuples"]})
            self.report["reference_receipts"].append(receipt)
        samples, lessons = [], []
        for seed in range(first_seed, first_seed + self.options.window_seeds):
            for start in range(self.options.window_starts):
                location = {"band": band, "sampler": "windows", "seed": seed, "start": start}
                current = [reference_samples.get((seed, si)) for si in range(start, start + 7)]
                if any(sample is None for sample in current):
                    self.fail("window_incomplete_lesson", location)
                    continue
                try:
                    samples.extend(current)
                    lessons.append(self.lesson(current, location))
                except Exception as exc:
                    self.error("window_lesson_validation", exc, location)
        requested = self.options.window_seeds * self.options.window_starts
        result = self.summarize(samples, lessons, requested)
        result["generated_schedule_length_per_seed"] = length
        result["seed_start_inclusive"] = first_seed
        result["seed_end_exclusive"] = first_seed + self.options.window_seeds
        result["labeled_schedule_unique_seed_sample_tuples"] = len(reference_samples)
        result["cyclic_start_counts"] = dict(Counter(str(lesson["start"] % 3) for lesson in lessons))
        return result

    def run(self):
        try:
            metadata = self.setup()
            self.canonical(metadata)
            for band in self.options.bands:
                print(f"Auditing {band}: {self.options.count} public Catalog lessons and "
                      f"{self.options.window_seeds * self.options.window_starts} overlapping windows", flush=True)
                self.report["bands"][band] = {}
                self.report["bands"][band]["catalog"] = self.catalog_band(band)
                self.report["bands"][band]["windows"] = self.window_band(band)
                streams = self.report["bands"][band]
                all_lessons = [lesson for stream in streams.values() for lesson in stream["lessons"]]
                streams["combined_counts"] = {
                    "completed_lessons": len(all_lessons),
                    "pair_occurrences_in_lessons": sum(len(lesson["input_sha256"]) for lesson in all_lessons),
                    "unique_input_hashes": len({sha for lesson in all_lessons for sha in lesson["input_sha256"]}),
                    "unique_seed_sample_tuples": len({(lesson["seed"], si) for lesson in all_lessons for si in lesson["sample_indices"]})}
        except Exception as exc:
            self.error("probe_setup_or_execution", exc)
        if self.source is not None:
            final_hash = file_hash(self.source)
            self.report["source_identity"]["generator_sha256_final"] = final_hash
            self.report["source_identity"]["source_unchanged"] = final_hash == self.source_start
            if final_hash != self.source_start:
                self.fail("source_changed_during_audit", {"sha256_start": self.source_start, "sha256_final": final_hash})
        self.report["finished_utc"] = datetime.now(timezone.utc).isoformat()
        self.report["required_lesson_count_per_band"] = 100
        self.report["meets_required_lesson_count"] = (
            bool(self.report["bands"]) and all(
                value.get("catalog", {}).get("completed_lessons", 0) >= 100
                for value in self.report["bands"].values()))
        self.report["audit_scope"] = "full_distribution" if self.report["meets_required_lesson_count"] else "smoke_or_debug"
        self.report["passed"] = not self.report["failures"] and not self.report["errors"]
        self.report["failure_count"] = len(self.report["failures"])
        self.report["error_count"] = len(self.report["errors"])
        self.options.out.parent.mkdir(parents=True, exist_ok=True)
        self.options.out.write_text(json.dumps(self.report, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"passed": self.report["passed"], "failures": self.report["failure_count"],
                          "errors": self.report["error_count"], "report": str(self.options.out)}), flush=True)
        return 0 if self.report["passed"] else 1


def parser():
    result = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    result.add_argument("--out", type=Path, required=True, help="JSON evidence path (existing file is replaced)")
    result.add_argument("--library", type=Path, default=Path(__file__).resolve().parents[3], help="ARCpuzzles repository root")
    result.add_argument("--count", type=int, default=100, help="independent public Catalog lessons per band (default 100; positive smaller counts permit smoke/debug runs)")
    result.add_argument("--seed", type=int, default=271828, help="fixed seed root for independent Catalog lessons")
    result.add_argument("--window-seeds", type=int, default=9, help="number of reproducible seeds for overlapping windows")
    result.add_argument("--window-starts", type=int, default=12, help="all schedule starts 0..N-1 for each window seed")
    result.add_argument("--bands", nargs="+", choices=("easy", "medium", "hard"), default=["easy", "medium", "hard"])
    result.add_argument("--timeout", type=float, default=600, help="seconds allowed per public generate/apply call")
    result.add_argument("--example-limit", type=int, default=3, help="compact full-grid examples retained per failure category")
    return result


def main(argv=None):
    cli = parser()
    options = cli.parse_args(argv)
    if options.count < 1:
        cli.error("--count must be positive")
    if options.window_seeds < 1 or options.window_starts < 3:
        cli.error("window seeds must be positive and starts must be at least 3 to cover cyclic starts")
    if options.example_limit < 1 or options.timeout <= 0:
        cli.error("example limit and timeout must be positive")
    if len(set(options.bands)) != len(options.bands):
        cli.error("bands must not repeat")
    return Audit(options).run()


if __name__ == "__main__":
    sys.exit(main())
