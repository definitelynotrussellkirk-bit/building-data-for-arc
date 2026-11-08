#!/usr/bin/env python3
"""Bounded, source-bound self-review of the native parametric prototype.

Run from the packet through ``review.py run --receipt ... python3 .../audit.py``.
Every rival is fitted to demonstrations only.  Query disagreements are reported
after fitting and never remove a surviving rival.  Output is compact JSON; a
passing finite audit is neither native acceptance nor training admission.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
import time

sys.dont_write_bytecode = True
HOME = Path(__file__).resolve().parent
TASK = "cae2423a6477"


def load_local(name):
    path = HOME / (name + ".py")
    spec = importlib.util.spec_from_file_location(
        "cae2423a6477_audit_" + name + "_" + hashlib.sha256(str(path).encode()).hexdigest()[:12], path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


RIVALS = load_local("rivals")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def source_inventory(root):
    sources = [path for path in HOME.iterdir() if path.is_file() and path.suffix in (".py", ".rkt", ".json")]
    sources += [root / "generators" / TASK / "generator.py",
                root / "generators" / TASK / "tests" / "test_parametric_rivals.py"]
    return {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(set(sources)) if path.is_file()}


def screen_episode(episode, mode, predictors=None):
    """Keep demonstration survivors, then measure their private-query errors."""
    candidates = RIVALS.bank(mode) if predictors is None else predictors
    result = {"survivors": [], "refutations": {}, "query_disagreements": {},
              "errors": [], "demonstration_evaluations": 0, "rival_lesson_combinations": 0}
    for name, predict in candidates.items():
        result["rival_lesson_combinations"] += 1
        try:
            for index, pair in enumerate(episode["train"]):
                result["demonstration_evaluations"] += 1
                if predict(pair["input"]) != pair["output"]:
                    result["refutations"][name] = index
                    break
            else:
                result["survivors"].append(name)
                disagreements = [index for index, pair in enumerate(episode["test"])
                                 if predict(pair["input"]) != pair["output"]]
                if disagreements:
                    result["query_disagreements"][name] = disagreements
        except Exception as error:
            result["errors"].append({"rival": name, "error": type(error).__name__ + ": " + str(error)})
    return result


def runtime_paths():
    for ancestor in HOME.parents:
        candidates = (ancestor / "shared" / "runtime", ancestor)
        found = next((path for path in candidates if (path / "reviewer_support.py").is_file()), None)
        if found is not None:
            sys.path.insert(0, str(found))
            break
    from reviewer_support import find_root
    root = find_root(__file__)
    nested = root / "shared" / "runtime"
    runtime = nested if (nested / "arc_repl" / "racket_bridge.py").is_file() else root
    if (root / "src").is_dir():
        sys.path.insert(0, str(root / "src"))
    return root, runtime


def _grid(rows):
    return [[int(value) for value in row] for row in rows]


def _visible_inputs(episode):
    return {split: [pair["input"] for pair in episode[split]] for split in ("train", "test")}


def _transforms(grid):
    result = []
    rotated = copy.deepcopy(grid)
    for turn in range(4):
        for reflected in (False, True):
            value = [row[::-1] for row in rotated] if reflected else copy.deepcopy(rotated)
            result.append((f"rotate_{90 * turn}" + ("_reflect" if reflected else ""), value))
        rotated = [list(row) for row in zip(*rotated[::-1])]
    return result


def run(seeds, demo_counts, queries=4, protected_seeds=(0, 17)):
    root, runtime = runtime_paths()
    from arcpuzzles import Catalog
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator
    started = time.monotonic()
    before = source_inventory(root)
    report = {
        "schema": "cae2423a6477-independent-parametric-audit-v1", "task_id": TASK,
        "status": "running", "source_sha256": before,
        "scope": {"seeds": list(seeds), "demo_counts": list(demo_counts), "queries": queries,
                  "modes": list(RIVALS.MODES), "protected_seeds": list(protected_seeds)},
        "checks": {"episodes": 0, "independent_label_comparisons": 0, "determinism": 0,
                   "global_rng_purity": 0, "matched_inputs": 0, "distinct_inputs": 0,
                   "demo_count_prefixes": 0, "query_count_prefixes": 0,
                   "finite_setting_identification": 0, "rival_lesson_combinations": 0,
                   "demonstration_evaluations": 0, "canonical_pairs": 0},
        "errors": [], "surviving_rivals": [], "query_disagreements": [],
        "teaching": {}, "protected": {"actual_executions": 0, "cache_hits": 0,
                                       "generated_label_comparisons": 0,
                                       "rival_refutation_comparisons": 0,
                                       "fixture_comparisons": 0, "d4_comparisons": 0,
                                       "refutation_witnesses": []},
        "limits": ["Finite declared rival grammar and sampled seeds only.",
                   "Signature equality is observed on the recorded controls, not a global equivalence proof.",
                   "Protected execution verifies this audit's labels and counterexamples, not native acceptance.",
                   "No production rule, production approval, or training admission is changed."],
    }
    checks = report["checks"]

    def failure(kind, **detail):
        report["errors"].append({"kind": kind, **detail})

    adapter = load_local("adapter")
    report["program_sha256"] = {mode: hashlib.sha256(adapter.program(
        {"completion_mode": mode}).encode()).hexdigest() for mode in RIVALS.MODES}
    selected = Catalog(root).get(TASK)
    canonical_programs = {row["program_solution"] for row in selected["variants"]
                          if isinstance(row.get("program_solution"), str)}
    default_program = adapter.program({"completion_mode": "border"})
    if canonical_programs != {default_program}:
        failure("canonical_default_not_byte_exact")
    seen_canonical = set()
    for row in selected["variants"]:
        testing = row.get("test", [])
        pairs = row.get("train", []) + ([testing] if isinstance(testing, dict) else testing)
        for pair in pairs:
            source, target = _grid(pair["input"]), _grid(pair["output"])
            marker = digest((source, target))
            if marker in seen_canonical:
                continue
            seen_canonical.add(marker)
            checks["canonical_pairs"] += 1
            if RIVALS.intended(source, "border") != target:
                failure("independent_oracle_canonical_disagreement", pair_sha256=marker)

    cache = {}
    screens = {}
    matched = {}
    all_controls = list(RIVALS.fixtures().values())
    report["teaching"] = {mode: {"named_rivals": len(RIVALS.bank(mode)),
        "refutation_counts": {name: 0 for name in RIVALS.bank(mode)},
        "rival_program_sha256": {name: hashlib.sha256(RIVALS.racket(mode, name).encode()).hexdigest()
                                 for name in RIVALS.bank(mode)}} for mode in RIVALS.MODES}
    for seed in seeds:
        for mode in RIVALS.MODES:
            previous = None
            settings = {"completion_mode": mode}
            for demos in demo_counts:
                location = {"seed": seed, "mode": mode, "demos": demos, "queries": queries}
                try:
                    state = random.getstate()
                    episode = adapter.generate(seed, settings.copy(), demos, queries)
                    checks["episodes"] += 1
                    if random.getstate() != state:
                        failure("global_random_state_changed", **location)
                    checks["global_rng_purity"] += 1
                    repeated = adapter.generate(seed, settings.copy(), demos, queries)
                    if repeated != episode:
                        failure("nondeterministic_generation", **location)
                    checks["determinism"] += 1
                    if episode.get("program_solution") != adapter.program(settings.copy()):
                        failure("returned_program_mismatch", **location)
                    if len(episode["train"]) != demos or len(episode["test"]) != queries:
                        failure("wrong_requested_counts", **location)
                    pairs = episode["train"] + episode["test"]
                    if len({digest(pair["input"]) for pair in pairs}) != len(pairs):
                        failure("duplicate_input_within_episode", **location)
                    checks["distinct_inputs"] += 1
                    for split in ("train", "test"):
                        for index, pair in enumerate(episode[split]):
                            wanted = RIVALS.intended(pair["input"], mode)
                            checks["independent_label_comparisons"] += 1
                            if wanted != pair["output"]:
                                failure("independent_label_disagreement", split=split, index=index, **location)
                    inputs = _visible_inputs(episode)
                    peer_key = seed, demos
                    if peer_key in matched and matched[peer_key] != inputs:
                        failure("setting_leaks_into_input_sampler", **location)
                    matched[peer_key] = inputs
                    checks["matched_inputs"] += 1
                    if previous is not None:
                        if episode["train"][:len(previous["train"])] != previous["train"] or episode["test"] != previous["test"]:
                            failure("demo_count_changes_existing_pairs", **location)
                        checks["demo_count_prefixes"] += 1
                    previous = episode
                    survivors = [candidate for candidate in RIVALS.MODES if all(
                        RIVALS.intended(pair["input"], candidate) == pair["output"] for pair in episode["train"])]
                    if survivors != [mode]:
                        failure("finite_settings_not_identified", candidates=survivors, **location)
                    checks["finite_setting_identification"] += 1
                    screen = screen_episode(episode, mode)
                    for count in ("rival_lesson_combinations", "demonstration_evaluations"):
                        checks[count] += screen[count]
                    for name in screen["refutations"]:
                        report["teaching"][mode]["refutation_counts"][name] += 1
                    for error in screen["errors"]:
                        failure("rival_execution_error", **error, **location)
                    if screen["survivors"]:
                        report["surviving_rivals"].append({**location, "rivals": screen["survivors"]})
                    if screen["query_disagreements"]:
                        report["query_disagreements"].append({**location, "rivals": screen["query_disagreements"]})
                    cache[seed, mode, demos] = episode
                    screens[seed, mode, demos] = screen
                    if demos == min(demo_counts):
                        all_controls.extend(pair["input"] for pair in episode["train"])
                except Exception as error:
                    failure("episode_error", error=type(error).__name__ + ": " + str(error), **location)

            # Count prefixes are a separate API check: shorter requests must
            # expose the same demonstrations and initial private queries.
            full = cache.get((seed, mode, min(demo_counts)))
            if full is not None:
                for short_count in range(1, queries):
                    try:
                        shorter = adapter.generate(seed, settings.copy(), min(demo_counts), short_count)
                        if shorter["train"] != full["train"] or shorter["test"] != full["test"][:short_count]:
                            failure("query_count_changes_existing_pairs", seed=seed, mode=mode, queries=short_count)
                        checks["query_count_prefixes"] += 1
                    except Exception as error:
                        failure("query_prefix_error", seed=seed, mode=mode, queries=short_count,
                                error=type(error).__name__ + ": " + str(error))

    for mode in RIVALS.MODES:
        groups = RIVALS.signature_groups(mode, all_controls)
        report["teaching"][mode]["observed_signature_classes"] = len(groups)
        report["teaching"][mode]["observed_equivalent_groups"] = [group for group in groups if len(group) > 1]
        report["teaching"][mode]["signature_control_count"] = len(all_controls)

    stress = RIVALS.fixtures()["dense_30"]
    report["stress_30x30"] = {mode: RIVALS.feature_summary(stress, mode) for mode in RIVALS.MODES}
    stress_features = report["stress_30x30"]["enclosed"]
    if (stress_features["green_cells"] < 250 or min(stress_features["quadrant_nonzero"]) < 40 or
            stress_features["collective_fill_cells"] == 0):
        failure("insufficient_30x30_stress", features=stress_features)

    try:
        with _local_imports(runtime, HOME):
            apply, identity, bridge = _real_evaluator(runtime)
            report["protected"]["runtime"] = identity
            executed = {}
            retained_witnesses = set()

            def execute(program, grid):
                key = program, digest(grid)
                if key in executed:
                    report["protected"]["cache_hits"] += 1
                    return executed[key]
                report["protected"]["actual_executions"] += 1
                result = apply(program, copy.deepcopy(grid))
                executed[key] = result
                return result

            try:
                for mode in RIVALS.MODES:
                    program = adapter.program({"completion_mode": mode})
                    for fixture_name, grid in RIVALS.fixtures().items():
                        target = RIVALS.intended(grid, mode)
                        for reference_name, source in (("adapter", program), ("independent", RIVALS.racket(mode))):
                            report["protected"]["fixture_comparisons"] += 1
                            if execute(source, grid) != target:
                                failure("protected_fixture_disagreement", mode=mode, fixture=fixture_name, reference=reference_name)
                    for seed in protected_seeds:
                        for demos in sorted({min(demo_counts), max(demo_counts)}):
                            episode = cache.get((seed, mode, demos))
                            if episode is None:
                                continue
                            for split in ("train", "test"):
                                for index, pair in enumerate(episode[split]):
                                    report["protected"]["generated_label_comparisons"] += 1
                                    if execute(program, pair["input"]) != pair["output"]:
                                        failure("protected_generated_disagreement", seed=seed, mode=mode,
                                                demos=demos, split=split, index=index)
                            for name, index in screens[seed, mode, demos]["refutations"].items():
                                pair = episode["train"][index]
                                predicted = RIVALS.bank(mode)[name](pair["input"])
                                actual = execute(RIVALS.racket(mode, name), pair["input"])
                                report["protected"]["rival_refutation_comparisons"] += 1
                                if actual != predicted or actual == pair["output"]:
                                    failure("protected_rival_refutation_disagreement", seed=seed,
                                            mode=mode, demos=demos, rival=name, demo_index=index)
                                if (mode, name) not in retained_witnesses:
                                    retained_witnesses.add((mode, name))
                                    report["protected"]["refutation_witnesses"].append({
                                        "seed": seed, "mode": mode, "demos": demos, "queries": queries,
                                        "rival": name, "demo_index": index,
                                        "input_sha256": digest(pair["input"]),
                                        "expected_sha256": digest(pair["output"]),
                                        "rival_output_sha256": digest(actual)})

                    # Covariance uses both a non-square adversarial input and a
                    # nested scene with asymmetric green contents.  Repeated
                    # transforms are counted as comparisons, not executions.
                    for fixture_name in ("perimeter_spoof", "nested_with_contents"):
                        grid = RIVALS.fixtures()[fixture_name]
                        target = RIVALS.intended(grid, mode)
                        transformed_targets = dict(_transforms(target))
                        for transform, changed in _transforms(grid):
                            wanted = transformed_targets[transform]
                            if RIVALS.intended(changed, mode) != wanted:
                                failure("independent_d4_disagreement", mode=mode, fixture=fixture_name, transform=transform)
                            report["protected"]["d4_comparisons"] += 1
                            if execute(program, changed) != wanted:
                                failure("protected_d4_disagreement", mode=mode, fixture=fixture_name, transform=transform)
            finally:
                bridge.close()
    except Exception as error:
        failure("protected_execution_error", error=type(error).__name__ + ": " + str(error))

    after = source_inventory(root)
    report["source_stable"] = before == after
    if before != after:
        failure("source_changed_during_audit", after_sha256=after)
    report["status"] = "passed" if not report["errors"] and not report["surviving_rivals"] else "failed"
    report["elapsed_seconds"] = round(time.monotonic() - started, 3)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2, 3, 8, 17, 31, 2**63 - 1])
    parser.add_argument("--demos", nargs="+", type=int, default=[2, 3, 4, 5, 6])
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--protected-seeds", nargs="+", type=int, default=[0, 17])
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error("audit output already exists; use a fresh source-bound receipt")
    if any(seed < 0 or seed > 2**63 - 1 for seed in args.seeds) or len(set(args.seeds)) != len(args.seeds):
        parser.error("seeds must be distinct integers in 0..2^63-1")
    if sorted(set(args.demos)) != args.demos or any(count < 2 or count > 6 for count in args.demos):
        parser.error("demo counts must be an ascending subset of 2..6")
    if not 1 <= args.queries <= 4:
        parser.error("query count must be in 1..4")
    if not set(args.protected_seeds) <= set(args.seeds):
        parser.error("protected seeds must be included in the generated audit scope")
    try:
        report = run(args.seeds, args.demos, args.queries, args.protected_seeds)
    except Exception as error:
        report = {"schema": "cae2423a6477-independent-parametric-audit-v1", "task_id": TASK,
                  "status": "failed", "errors": [{"kind": "audit_setup_error",
                  "error": type(error).__name__ + ": " + str(error)}]}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "out": str(args.out), "checks": report.get("checks"),
                      "protected_executions": report.get("protected", {}).get("actual_executions"),
                      "errors": len(report.get("errors", [])),
                      "surviving_lessons": len(report.get("surviving_rivals", []))}, separators=(",", ":")))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
