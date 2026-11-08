#!/usr/bin/env python3
"""Source-bound lesson census for this task, using only public reference APIs.

Run through the packet's run_with_racket.py; see LESSON_PROBE.md.  The probe
enumerates the selected generator's declarations rather than maintaining a
second rival list.  Output directories must be new so earlier failures survive.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import inspect
import json
from pathlib import Path
import sys
import time
import traceback
import types


REPO = Path(__file__).resolve().parents[3]
TASK_ID = Path(__file__).resolve().parents[1].name
GENERATOR = REPO / "generators" / TASK_ID / "generator.py"
BANDS = ("easy", "medium", "hard")
N_TRAIN, N_TEST, PERIOD = 3, 2, 3
CATEGORIES = (
    "refuted_in_demos",
    "survives_demos_agrees_queries",
    "survives_demos_disagrees_queries",
    "rival_error",
)


def compact(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(compact(value).encode()).hexdigest()


def file_digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def grid(value):
    """Normalize the canonical row-string format and reject malformed grids."""
    if isinstance(value, list) and value and all(isinstance(row, str) for row in value):
        value = [[int(cell) for cell in row] for row in value]
    if (not isinstance(value, list) or not 1 <= len(value) <= 30
            or not all(isinstance(row, list) for row in value)
            or not 1 <= len(value[0]) <= 30
            or any(len(row) != len(value[0]) for row in value)
            or any(type(cell) is not int or not 0 <= cell <= 9
                   for row in value for cell in row)):
        raise ValueError("expected a rectangular 1..30 by 1..30 integer 0..9 grid")
    return deepcopy(value)


def load_generator():
    # Read/compile exactly the bytes being hashed, without a stale .pyc cache.
    for path in (REPO / "src", REPO / "shared/runtime"):
        sys.path.insert(0, str(path))
    name = "lesson_probe_generator_" + TASK_ID
    module = types.ModuleType(name)
    module.__file__ = str(GENERATOR)
    sys.modules[name] = module
    exec(compile(GENERATOR.read_bytes(), str(GENERATOR), "exec"), module.__dict__)
    return module


def call_reasons(hook, *values, difficulty=None, allow_bool=False):
    copies = deepcopy(values)
    params = inspect.signature(hook).parameters
    kwargs = ({"difficulty": difficulty} if difficulty is not None and
              ("difficulty" in params or any(p.kind == p.VAR_KEYWORD for p in params.values()))
              else {})
    result = hook(*copies, **kwargs)
    if copies != values:
        raise ValueError("hook mutated its input")
    if allow_bool and type(result) is bool:
        return [] if result else ["predicate returned False"]
    if not isinstance(result, list) or not all(isinstance(item, str) for item in result):
        raise TypeError("hook must return list[str]" + (" or bool" if allow_bool else ""))
    return result


class Probe:
    def __init__(self, args):
        self.args = args
        self.out = args.out.resolve()
        self.out.mkdir(parents=True, exist_ok=False)
        self.started = time.monotonic()
        self.streams = {}
        self.failures = []
        self.pairs = {}
        self.predictions = {}
        self.programs = set()
        self.evidence_seen = set()
        self.population = {}
        self.calls = []
        self.rivals = {}
        self.shortcuts = {}
        self.source_paths = {
            "generator": GENERATOR,
            "canonical_file": REPO / "shared/data/canonical/puzzles.jsonl",
            "public_catalog": REPO / "src/arcpuzzles/catalog.py",
            "public_runtime": REPO / "src/arcpuzzles/runtime.py",
            "worker": REPO / "src/arcpuzzles/worker.py",
            "probe": Path(__file__).resolve(),
        }
        self.source_hashes = {key: file_digest(path) for key, path in self.source_paths.items()}
        # These small snapshots preserve the exact measured implementation even
        # when a later iteration edits the selected generator or this probe.
        for key in ("generator", "probe"):
            data = self.source_paths[key].read_bytes()
            if hashlib.sha256(data).hexdigest() != self.source_hashes[key]:
                raise RuntimeError(f"{key} changed while taking the source snapshot")
            (self.out / f"{key}_source.py").write_bytes(data)
        self.summary = {
            "schema": "59c2f0a5d4a9-lesson-probe-v1",
            "task_id": TASK_ID,
            "phase": args.phase,
            "started_utc": utc_now(),
            "invocation": {"cwd": str(Path.cwd()), "argv": [sys.executable, *sys.argv]},
            "source": {"sha256": self.source_hashes,
                       "paths": {key: str(path.relative_to(REPO))
                                 for key, path in self.source_paths.items()}},
            "policy": {
                "requested_lessons_per_band": args.lessons,
                "minimum_final_lessons_per_band": 100,
                "n_train": N_TRAIN, "n_test": N_TEST, "overrides": {},
                "reference": "canonical", "allow_unapproved": True,
                "actual_runner": "Catalog.generate, with counts split equally across cyclic starts 0,1,2; remainder assigned to earlier starts",
                "runner_seed_policy": "seed argument + episode_index; each call records its seed range",
                "runner_index_policy": "each episode starts at the requested sample_index; accepts five distinct validated pairs from at most 25 consecutive attempts; first three accepted pairs are demos and next two are queries",
                "direct_cyclic_windows": "one new seed per band; generate indices 0..6 once; apply canonical Racket with Catalog.apply; inspect windows 0..4, 1..5, 2..6",
                "cyclic_period": PERIOD,
                "replay_check": "regenerate every actual accepted input with the same seed, index, difficulty; require exact grid equality",
                "apply_batch_limit": 64,
                "classification": {
                    "refuted_in_demos": "at least one demo output differs, with every rival call valid",
                    "survives_demos_agrees_queries": "all three demos and both queries agree",
                    "survives_demos_disagrees_queries": "all three demos agree and at least one query differs",
                    "rival_error": "a rival raises, mutates its input, or returns an invalid grid; never counted as a successful refutation",
                },
                "domain_limits": "This measures default draws only, in the named difficulty bands and finite seed/index ranges. Explicit axis overrides can supersede the teaching schedule. No universal induction or guarantee for undeclared rivals is claimed.",
            },
        }

    def write(self, name, value):
        if name not in self.streams:
            self.streams[name] = (self.out / name).open("x", encoding="utf-8")
        self.streams[name].write(compact(value) + "\n")
        self.streams[name].flush()

    def fail(self, kind, **details):
        entry = {"failure_index": len(self.failures), "kind": kind, **details}
        self.failures.append(entry)
        self.write("failures.jsonl", entry)

    def bound(self):
        current = {key: file_digest(path) for key, path in self.source_paths.items()}
        if current != self.source_hashes:
            raise RuntimeError("source bytes changed during the probe: " + compact(current))

    def declarations(self):
        memberships = {}
        for attribute in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS"):
            declared = getattr(self.module, attribute, None)
            if not isinstance(declared, dict) or not declared:
                self.fail("invalid_declaration", attribute=attribute,
                          reason="expected a nonempty dict[str, callable]")
                continue
            for name, function in declared.items():
                if not isinstance(name, str) or not name or not callable(function):
                    self.fail("invalid_declaration_entry", attribute=attribute, name=repr(name))
                    continue
                if name in self.rivals and self.rivals[name] is not function:
                    self.fail("conflicting_rival_name", name=name, attribute=attribute)
                    raise ValueError("a rival name denotes different callables across declarations")
                self.rivals[name] = function
                memberships.setdefault(name, []).append(attribute)
                if attribute == "CANONICAL_SHORTCUTS":
                    self.shortcuts[name] = function
        self.summary["declarations"] = {
            name: {"memberships": memberships[name],
                   "callable": function.__qualname__,
                   "source_line": getattr(getattr(function, "__code__", None), "co_firstlineno", None)}
            for name, function in self.rivals.items()
        }
        if not self.rivals or not self.shortcuts:
            raise ValueError("the required rival declarations are incomplete")

    def prediction(self, name, input_grid):
        key = (name, digest(input_grid))
        if key in self.predictions:
            return self.predictions[key]
        copied = deepcopy(input_grid)
        try:
            output = grid(self.rivals[name](copied))
            if copied != input_grid:
                raise ValueError("rival mutated its input")
            result = {"output": output, "output_sha256": digest(output), "error": None}
        except Exception as exc:
            result = {"output": None, "output_sha256": None,
                      "error": f"{type(exc).__name__}: {exc}"}
        self.predictions[key] = result
        return result

    def register_pair(self, input_grid, output_grid):
        input_grid, output_grid = grid(input_grid), grid(output_grid)
        ih, oh = digest(input_grid), digest(output_grid)
        if ih in self.pairs:
            if self.pairs[ih]["output"] != output_grid:
                self.fail("inconsistent_reference_output", input_sha256=ih,
                          old_output=self.pairs[ih]["output"], new_output=output_grid)
            return ih
        pair = {"input_sha256": ih, "output_sha256": oh,
                "pair_sha256": digest({"input": input_grid, "output": output_grid}),
                "input": input_grid, "output": output_grid}
        self.pairs[ih] = pair
        self.write("pairs.jsonl", pair)
        return ih

    def apply(self, inputs, label):
        outputs = []
        for offset in range(0, len(inputs), 64):
            self.bound()
            batch = inputs[offset:offset + 64]
            try:
                receipt = self.catalog.apply(TASK_ID, batch, reference="canonical",
                                             allow_unapproved=True, timeout=self.args.timeout)
            except Exception as exc:
                self.fail("public_application_failure", label=label, offset=offset,
                          inputs=batch, error=f"{type(exc).__name__}: {exc}",
                          public_failure_receipt=getattr(exc, "run", None))
                raise
            self.write("apply_receipts.jsonl", {"label": label, "offset": offset,
                                               "public_method": "Catalog.apply", "receipt": receipt})
            if (receipt["generator_sha256"] != self.source_hashes["generator"]
                    or receipt["executed_rule_hash"] != self.rule_hash
                    or not receipt["rule_hash_matches_catalog"]):
                self.fail("apply_source_mismatch", label=label, offset=offset, receipt=receipt)
            if len(receipt["results"]) != len(batch):
                raise ValueError("Catalog.apply returned an incorrect result count")
            for result in receipt["results"]:
                if not result.get("valid_output") or result.get("error"):
                    self.fail("reference_application", label=label, result=result)
                    outputs.append(None)
                else:
                    outputs.append(grid(result["output"]))
        return outputs

    def canonical(self, variants):
        usable, skipped = [], []
        for vi, variant in enumerate(variants):
            for split in ("train", "test"):
                raw = variant.get(split, [])
                items = [raw] if isinstance(raw, dict) else raw if isinstance(raw, list) else []
                if not isinstance(raw, (dict, list)):
                    skipped.append({"variant": vi, "split": split, "reason": "invalid pair container"})
                for pi, pair in enumerate(items):
                    locator = {"variant": vi, "split": split, "pair_index": pi}
                    try:
                        if not isinstance(pair, dict) or "output" not in pair:
                            raise ValueError("no labeled output")
                        usable.append({**locator, "input": grid(pair["input"]),
                                       "canonical_output": grid(pair["output"])})
                    except (ValueError, KeyError, TypeError) as exc:
                        skipped.append({**locator, "reason": str(exc)})
        if not usable:
            self.fail("no_usable_canonical_pairs")
            raise ValueError("no usable canonical pairs")
        outputs = self.apply([pair["input"] for pair in usable], "canonical")
        stats = {name: Counter() for name in self.rivals}
        for pair, output in zip(usable, outputs, strict=True):
            pair["reference_output"] = output
            pair["input_sha256"] = digest(pair["input"])
            pair["reference_matches_canonical"] = (output == pair["canonical_output"]
                                                     if output is not None else None)
            if output is not None:
                self.register_pair(pair["input"], output)
            if pair["reference_matches_canonical"] is False:
                self.fail("canonical_reference_mismatch", pair=pair)
            predictions = {}
            for name in self.rivals:
                prediction = self.prediction(name, pair["input"])
                agrees = not prediction["error"] and prediction["output"] == pair["canonical_output"]
                category = "error" if prediction["error"] else "fits" if agrees else "disagrees"
                stats[name][category] += 1
                predictions[name] = {**prediction, "matches_canonical": agrees}
                if name in self.shortcuts and not agrees:
                    self.fail("claimed_canonical_shortcut_does_not_fit", rival=name,
                              pair={key: pair[key] for key in ("variant", "split", "pair_index", "input_sha256")},
                              prediction=prediction)
            pair["rivals"] = predictions
        self.summary["canonical"] = {
            "variants": len(variants), "usable_pairs": len(usable), "skipped_pairs": skipped,
            "unique_input_count": len({digest(pair["input"]) for pair in usable}),
            "reference_verified_pairs": sum(pair["reference_matches_canonical"] is True for pair in usable),
            "reference_disagreement_pairs": sum(pair["reference_matches_canonical"] is False for pair in usable),
            "unavailable_reference_outputs": sum(pair["reference_output"] is None for pair in usable),
            "rivals": {name: {"denominator": len(usable), "claimed_canonical_shortcut": name in self.shortcuts,
                              **{key: counts[key] for key in ("fits", "disagrees", "error")}}
                       for name, counts in stats.items()},
        }
        (self.out / "canonical.json").write_text(json.dumps({"summary": self.summary["canonical"],
                                                           "pairs": usable}, indent=2) + "\n")

    def population_for(self, source, band):
        return self.population.setdefault((source, band), {
            "lessons": 0, "draw_occurrences": 0, "unique_inputs": set(),
            "unique_demo_inputs": set(), "unique_query_inputs": set(),
            "starts": Counter(), "seeds": [], "accepted_sample_indices": set(),
            "nonconsecutive_lessons": 0, "rejections": 0,
            "rivals": {name: Counter() for name in self.rivals},
        })

    def lesson(self, source, band, seed, start, pairs, indices, *, episode=None, call_id=None):
        if len(pairs) != N_TRAIN + N_TEST or len(indices) != len(pairs):
            raise ValueError("lesson does not contain exactly three demos and two queries")
        pop = self.population_for(source, band)
        pop["lessons"] += 1
        pop["seeds"].append(seed)
        pop["starts"][start] += 1
        pop["accepted_sample_indices"].update(indices)
        hashes = [self.register_pair(pair["input"], pair["output"]) for pair in pairs]
        pop["draw_occurrences"] += len(pairs)
        pop["unique_inputs"].update(hashes)
        pop["unique_demo_inputs"].update(hashes[:N_TRAIN])
        pop["unique_query_inputs"].update(hashes[N_TRAIN:])
        consecutive = indices == list(range(start, start + len(pairs)))
        if not consecutive:
            pop["nonconsecutive_lessons"] += 1
        record = {"source": source, "band": band, "seed": seed,
                  "requested_start_index": start, "sample_indices": indices,
                  "consecutive_without_skips": consecutive, "call_id": call_id,
                  "train_input_sha256": hashes[:N_TRAIN], "query_input_sha256": hashes[N_TRAIN:],
                  "rivals": {}}
        if episode is not None:
            record["public_episode_metadata"] = {key: value for key, value in episode.items()
                                                if key not in {"train", "test", "program"}}
            record["public_episode_payload_sha256"] = digest(episode)
            record["program_sha256"] = hashlib.sha256(episode["program"].encode()).hexdigest()
            if record["program_sha256"] not in self.programs:
                self.programs.add(record["program_sha256"])
                self.write("programs.jsonl", {"program_sha256": record["program_sha256"],
                                             "program": episode["program"],
                                             "executed_rule_hash": episode["executed_rule_hash"]})
            pop["rejections"] += len(episode.get("rejections", []))
            for rejection in episode.get("rejections", []):
                self.fail("runner_rejection", band=band, call_id=call_id, rejection=rejection)
            if not consecutive:
                self.fail("runner_skipped_scheduled_index", band=band, seed=seed,
                          expected=list(range(start, start + len(pairs))), actual=indices)
        for name in self.rivals:
            predictions = [self.prediction(name, pair["input"]) for pair in pairs]
            errors = [i for i, prediction in enumerate(predictions) if prediction["error"]]
            agrees = [not prediction["error"] and prediction["output"] == pair["output"]
                      for prediction, pair in zip(predictions, pairs, strict=True)]
            if errors:
                category = "rival_error"
            elif not all(agrees[:N_TRAIN]):
                category = "refuted_in_demos"
            elif all(agrees[N_TRAIN:]):
                category = "survives_demos_agrees_queries"
            else:
                category = "survives_demos_disagrees_queries"
            pop["rivals"][name][category] += 1
            result = {"category": category, "demo_agreements": agrees[:N_TRAIN],
                      "query_agreements": agrees[N_TRAIN:],
                      "prediction_sha256": [prediction["output_sha256"] for prediction in predictions]}
            if errors:
                result["errors"] = [{"pair_index": i, "error": predictions[i]["error"]} for i in errors]
            record["rivals"][name] = result
            is_failure = category in {"rival_error", "survives_demos_disagrees_queries"}
            if is_failure:
                self.fail(category, source=source, band=band, seed=seed, start=start,
                          rival=name, inputs=hashes, result=result)
            key = (source, band, name, category)
            if key not in self.evidence_seen or is_failure:
                self.evidence_seen.add(key)
                # Full predictions make all harmful survivors and the first
                # decisive outcome for each rival/band directly inspectable.
                self.write("rival_evidence.jsonl", {"source": source, "band": band, "seed": seed,
                           "start": start, "sample_indices": indices, "rival": name, "category": category,
                           "input_sha256": hashes, "predictions": predictions})
        hook = getattr(self.module, "lesson_identifiable", None)
        if callable(hook):
            record["lesson_identifiable"] = []
            for qi, query in enumerate(pairs[N_TRAIN:]):
                try:
                    reasons = call_reasons(hook, pairs[:N_TRAIN], query)
                    record["lesson_identifiable"].append(reasons)
                    if reasons:
                        self.fail("lesson_hook_rejected", source=source, band=band,
                                  seed=seed, start=start, query_index=qi, reasons=reasons)
                except Exception as exc:
                    error = f"{type(exc).__name__}: {exc}"
                    record["lesson_identifiable"].append({"error": error})
                    self.fail("lesson_hook_error", source=source, band=band, seed=seed,
                              start=start, query_index=qi, error=error)
        self.write("lessons.jsonl", record)

    def runner_census(self):
        for bi, band in enumerate(BANDS):
            consumed = 0
            for start in range(PERIOD):
                count = self.args.lessons // PERIOD + (start < self.args.lessons % PERIOD)
                if not count:
                    continue
                seed = self.args.seed + bi * self.args.lessons + consumed
                consumed += count
                options = dict(count=count, seed=seed, difficulty=band, n_train=N_TRAIN,
                               n_test=N_TEST, sample_index=start, overrides={},
                               reference="canonical", allow_unapproved=True, timeout=self.args.timeout)
                call_id = len(self.calls)
                call = {"call_id": call_id, "method": "Catalog.generate", "task_id": TASK_ID,
                        "options": options, "requested_seed_range_inclusive": [seed, seed + count - 1]}
                self.calls.append(call)
                self.bound()
                print(f"[{band}] Catalog.generate: {count} lessons, start={start}, seeds={seed}..{seed + count - 1}", flush=True)
                try:
                    episodes = self.catalog.generate(TASK_ID, **options)
                except Exception as exc:
                    episodes = getattr(exc, "partial_episodes", [])
                    self.fail("public_generation_failure", call_id=call_id,
                              error=f"{type(exc).__name__}: {exc}",
                              public_failure_receipt=getattr(exc, "run", None))
                call["returned_lessons"] = len(episodes)
                if len(episodes) != count:
                    self.fail("incomplete_runner_census", call_id=call_id, expected=count, actual=len(episodes))
                for offset, episode in enumerate(episodes):
                    expected_seed = seed + offset
                    if episode.get("seed") != expected_seed or episode.get("episode_index") != offset:
                        self.fail("unexpected_runner_episode_identity", call_id=call_id,
                                  expected_seed=expected_seed, episode_index=episode.get("episode_index"),
                                  actual_seed=episode.get("seed"))
                    provenance = episode.get("provenance", {})
                    if (provenance.get("generator_sha256") != self.source_hashes["generator"]
                            or provenance.get("rule_hash") != self.rule_hash
                            or episode.get("executed_rule_hash") != self.rule_hash):
                        self.fail("runner_source_mismatch", call_id=call_id, provenance=provenance)
                    pairs = episode["train"] + episode["test"]
                    indices = episode["sample_indices"]
                    for index, pair in zip(indices, pairs, strict=True):
                        generated = self.module.generate(seed=episode["seed"], sample_index=index,
                                                         difficulty=band)
                        replay = grid(generated.get("input") if isinstance(generated, dict) else generated)
                        if replay != pair["input"]:
                            self.fail("runner_input_replay_mismatch", band=band, seed=episode["seed"],
                                      sample_index=index, runner_input=pair["input"], direct_input=replay)
                    self.lesson("actual_runner", band, episode["seed"], start, pairs, indices,
                                episode=episode, call_id=call_id)
                self.write("generate_calls.jsonl", call)

    def cyclic_census(self):
        for bi, band in enumerate(BANDS):
            seed = self.args.seed + len(BANDS) * self.args.lessons + bi
            inputs = []
            for index in range(PERIOD + N_TRAIN + N_TEST - 1):
                generated = self.module.generate(seed=seed, sample_index=index, difficulty=band)
                input_grid = grid(generated.get("input") if isinstance(generated, dict) else generated)
                checker = getattr(self.module, "self_check", None)
                if callable(checker):
                    reasons = call_reasons(checker, input_grid, difficulty=band)
                    if reasons:
                        self.fail("direct_input_self_check", band=band, seed=seed,
                                  sample_index=index, reasons=reasons, input=input_grid)
                inputs.append(input_grid)
            outputs = self.apply(inputs, f"direct_cyclic:{band}:seed={seed}")
            for start in range(PERIOD):
                indices = list(range(start, start + N_TRAIN + N_TEST))
                if any(outputs[index] is None for index in indices):
                    self.fail("unmaterialized_direct_window", band=band, seed=seed, start=start)
                    continue
                pairs = [{"input": inputs[index], "output": outputs[index]} for index in indices]
                self.lesson("direct_cyclic", band, seed, start, pairs, indices)

    def run(self):
        self.module = load_generator()
        from arcpuzzles import Catalog
        self.catalog = Catalog(REPO)
        description = self.catalog.get(TASK_ID)
        self.rule_hash = description["rule_hash"]
        self.summary["source"].update({
            "generator_version": getattr(self.module, "VERSION", None),
            "declared_rule_hash": getattr(self.module, "RULE_HASH", None),
            "catalog_rule_hash": self.rule_hash,
            "canonical_variants_sha256": digest(description["variants"]),
        })
        if description["generator_sha256"] != self.source_hashes["generator"]:
            raise RuntimeError("catalog generator hash differs from selected source")
        if getattr(self.module, "RULE_HASH", None) != self.rule_hash:
            self.fail("declared_rule_hash_mismatch", declared=getattr(self.module, "RULE_HASH", None),
                      catalog=self.rule_hash)
        self.declarations()
        self.canonical(description["variants"])
        self.runner_census()
        self.cyclic_census()
        self.bound()

    def finish(self):
        populations = {}
        for (source, band), pop in self.population.items():
            row = {key: value for key, value in pop.items()
                   if key not in {"unique_inputs", "unique_demo_inputs", "unique_query_inputs",
                                  "seeds", "accepted_sample_indices", "rivals", "starts"}}
            row.update({
                "denominator_lessons": pop["lessons"],
                "unique_input_count": len(pop["unique_inputs"]),
                "unique_demo_input_count": len(pop["unique_demo_inputs"]),
                "unique_query_input_count": len(pop["unique_query_inputs"]),
                "unique_input_hashes": sorted(pop["unique_inputs"]),
                "seed_range_inclusive": [min(pop["seeds"]), max(pop["seeds"])],
                "unique_seed_count": len(set(pop["seeds"])),
                "sample_indices_observed": sorted(pop["accepted_sample_indices"]),
                "cyclic_start_counts": dict(sorted(pop["starts"].items())),
                "rivals": {name: {"denominator_lessons": pop["lessons"],
                                  **{category: counts[category] for category in CATEGORIES}}
                           for name, counts in pop["rivals"].items()},
            })
            populations.setdefault(source, {})[band] = row
        self.summary["populations"] = populations
        self.summary["generate_calls"] = self.calls
        if self.args.phase == "final":
            for band in BANDS:
                measured = populations.get("actual_runner", {}).get(band, {}).get("lessons", 0)
                if measured < 100:
                    self.fail("insufficient_final_lessons", band=band, measured=measured, minimum=100)
                starts = populations.get("direct_cyclic", {}).get(band, {}).get("cyclic_start_counts", {})
                if any(starts.get(start, 0) == 0 for start in range(PERIOD)):
                    self.fail("missing_cyclic_start", band=band, observed=starts)
        current = {key: file_digest(path) for key, path in self.source_paths.items()}
        self.summary["source"]["sha256_at_finish"] = current
        if current != self.source_hashes:
            self.fail("final_source_drift", current=current)
        for stream in self.streams.values():
            stream.close()
        self.summary["failure_count"] = len(self.failures)
        self.summary["failure_kinds"] = dict(Counter(failure["kind"] for failure in self.failures))
        self.summary["status"] = "pass" if not self.failures else "fail"
        self.summary["completed_utc"] = utc_now()
        self.summary["elapsed_seconds"] = round(time.monotonic() - self.started, 3)
        self.summary["unique_inputs_all_sources"] = len(self.pairs)
        self.summary["all_measured_rivals_refuted_in_every_lesson"] = bool(self.population) and all(
            counts["refuted_in_demos"] == pop["lessons"]
            for pop in self.population.values() for counts in pop["rivals"].values())
        self.summary["pass_definition"] = (
            "No source/label/declaration/replay errors, rejected draws, incomplete batches, "
            "harmful surviving rivals, rival-call errors, or rejected lesson hooks; final "
            "runs also require >=100 actual-runner lessons per band and all direct cyclic starts. "
            "Surviving rivals agreeing on every query are reported separately and do not alone fail."
        )
        self.report()
        self.summary["artifacts"] = [{"path": path.name, "bytes": path.stat().st_size,
                                      "sha256": file_digest(path)}
                                     for path in sorted(self.out.iterdir()) if path.is_file()]
        (self.out / "summary.json").write_text(json.dumps(self.summary, indent=2) + "\n")
        print(compact({"status": self.summary["status"], "phase": self.args.phase,
                       "generator_sha256": self.source_hashes["generator"],
                       "rule_hash": self.summary["source"].get("catalog_rule_hash"),
                       "failure_count": len(self.failures), "summary": str(self.out / "summary.json")}), flush=True)
        return 0 if not self.failures else 1

    def report(self):
        text = [f"# Lesson probe: {TASK_ID}", "",
                f"Phase: **{self.args.phase}**. Result: **{self.summary['status']}**.", "",
                f"Generator SHA-256: `{self.source_hashes['generator']}`.", "",
                f"Catalog rule hash: `{self.summary['source'].get('catalog_rule_hash', 'unavailable')}`.", "",
                "## Measured populations", "",
                "| Source | Band | Lessons | Draw occurrences | Unique inputs | Starts 0 / 1 / 2 |",
                "| --- | --- | ---: | ---: | ---: | --- |"]
        for source, bands in self.summary["populations"].items():
            for band, pop in bands.items():
                starts = " / ".join(str(pop["cyclic_start_counts"].get(start, 0)) for start in range(PERIOD))
                text.append(f"| {source} | {band} | {pop['lessons']} | {pop['draw_occurrences']} | {pop['unique_input_count']} | {starts} |")
        text += ["", "## Every declared rival", "",
                 "| Source | Band | Rival | Demo refuted | Survives, query agrees | Survives, query differs | Errors | Denominator |",
                 "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |"]
        for source, bands in self.summary["populations"].items():
            for band, pop in bands.items():
                for name, counts in pop["rivals"].items():
                    values = " | ".join(str(counts[category]) for category in CATEGORIES)
                    text.append(f"| {source} | {band} | {name} | {values} | {pop['lessons']} |")
        text += ["", "## Evidence and limits", "",
                 "`canonical.json` checks every usable canonical train and labeled test pair against every declaration; the claimed-shortcut status comes from `CANONICAL_SHORTCUTS`. `apply_receipts.jsonl` retains the complete public Racket receipts for canonical and direct cyclic inputs.", "",
                 "`pairs.jsonl` stores each unique input and its Racket output once. `lessons.jsonl` refers to those hashes, records all rival agreements, and preserves the public episode metadata, actual indices, and rejected draws. `programs.jsonl` stores each executed program once, allowing the complete public episode and its payload hash to be reconstructed. `rival_evidence.jsonl` retains complete rival predictions for the first example of each observed outcome in each band/population, plus every harmful survivor or rival error. Input/output hashes use SHA-256 over compact sorted-key JSON (grids have no keys).", "",
                 "The direct cyclic windows overlap: each band has 15 draw occurrences but only seven index draws. Their denominators are reported separately from the actual public-runner population. The finite census uses default controls only; overrides and unlisted rival rules are outside its teaching claim.", "",
                 f"Failures retained: **{len(self.failures)}**. Failure kinds: `{compact(self.summary['failure_kinds'])}`. Read `failures.jsonl` when present; an exit code alone is not the evidence.", ""]
        (self.out / "REPORT.md").write_text("\n".join(text))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="new output directory; never overwritten")
    parser.add_argument("--lessons", type=int, default=100, help="actual Catalog.generate lessons per band (default: 100)")
    parser.add_argument("--seed", type=int, default=20261003, help="first seed; all exact ranges are recorded")
    parser.add_argument("--timeout", type=float, default=900, help="seconds allowed for each public API call")
    parser.add_argument("--phase", choices=("preliminary", "final"), default="final")
    args = parser.parse_args(argv)
    if args.lessons < 1 or args.timeout <= 0:
        parser.error("--lessons and --timeout must be positive")
    if args.phase == "final" and args.lessons < 100:
        parser.error("final evidence requires --lessons >= 100; use --phase preliminary for a diagnostic")
    probe = Probe(args)
    try:
        probe.run()
    except Exception as exc:
        probe.fail("probe_exception", error=f"{type(exc).__name__}: {exc}", traceback=traceback.format_exc())
    return probe.finish()


if __name__ == "__main__":
    raise SystemExit(main())
