"""Bounded, source-bound independent audit of the parametric header family.

Run through the packet wrapper.  The rival bank is authored independently of
the episode prototype.  Adapter labels are observed claims; expected labels
come from rivals.intended and representative protected-Racket executions.

The broad census uses eight seeds, every supported demonstration/query count,
and both modes.  Protected replay covers the complete hand fixture set,
canonical labels, each named rival's distinguishing fixture, selected legal
transformations, and the minimum/maximum demonstration requests at two seeds.
It deliberately does not execute a large redundant Racket cross-product.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from reviewer_support import canonical_pairs, find_root


sys.dont_write_bytecode = True
TASK_ID = "40e85135fbf8"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
DEFAULT_SEEDS = (0, 1, 2, 3, 7, 19, 41, 101)


def _load(path, stem):
    path = Path(path).resolve()
    name = stem + "_" + hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


independent = _load(HERE / "rivals.py", "independent_header_semantics")


def _encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def _grid_id(grid):
    return _sha(_encoded(grid).encode())


def _bindings():
    paths = [*HERE.glob("*.py"), *HERE.glob("*.rkt")]
    paths += [HERE / "promotion.json"] if (HERE / "promotion.json").is_file() else []
    test = HERE.parents[1] / "tests/test_parametric_rivals.py"
    if test.is_file():
        paths.append(test)
    return {str(path.relative_to(ROOT)): _sha(path.read_bytes()) for path in sorted(set(paths))}


def _output_grid(output):
    if (type(output) is not list or not 1 <= len(output) <= 30 or
            type(output[0]) is not list or not 1 <= len(output[0]) <= 30):
        return False
    return all(type(row) is list and len(row) == len(output[0]) and
               all(type(value) is int and 0 <= value <= 9 for value in row) for row in output)


def _transforms(grid):
    rows, cols = independent.headers(grid)
    permutation = [0, 8, 3, 7, 2, 9, 4, 1, 6, 5]
    return (
        ("transpose", independent.from_headers(cols, rows), lambda out: [list(row) for row in zip(*out)]),
        ("reverse_header_rows", independent.from_headers(rows[::-1], cols), lambda out: out[::-1]),
        ("reverse_header_columns", independent.from_headers(rows, cols[::-1]), lambda out: [row[::-1] for row in out]),
        ("color_permutation", [[permutation[value] for value in row] for row in grid],
         lambda out: [[permutation[value] for value in row] for row in out]),
    )


def run(phase, seeds):
    from arcpuzzles.parametric_worker import _local_imports as protected_local_imports, _real_evaluator

    before = _bindings()
    report = {
        "schema": "header-parametric-independent-audit-v1", "task_id": TASK_ID,
        "phase": phase, "source_bindings": before,
        "oracle_independence": "Python flood fill and hand fixtures were authored without reading the prototype; adapter is executed only to observe claims.",
        "seeds": list(seeds), "bank_counts": {mode: len(independent.bank(mode)) for mode in independent.MODES},
        "excluded_equivalences": ["monochromatic 4-versus-8 connectivity",
                                  "four-connected foreground versus monochromatic components",
                                  "component bounding-box area versus cell count",
                                  "maximal same-color header-run Cartesian products"],
        "counts": {}, "failures": [], "ambiguity_count": 0, "ambiguity_families": {},
        "first_ambiguity_per_rival": {}, "protected_labels": [], "fixtures": {},
        "demonstration_features": [], "query_features": [],
        "surviving_rivals_without_query_disagreement": {},
        "limits": "Finite declared-bank evidence over the stated seeds/counts and hand fixtures; no universal rule uniqueness or owner acceptance is claimed.",
    }
    counts = Counter()
    failure_counts = Counter()

    def fail(kind, **detail):
        failure_counts[kind] += 1
        if len(report["failures"]) < 30:
            report["failures"].append({"kind": kind, **detail})

    runtime = ROOT / "shared/runtime" if (ROOT / "shared/runtime/arc_repl").is_dir() else ROOT
    adapter = None
    if phase in {"episodes", "all"}:
        adapter = _load(HERE / "adapter.py", "independent_audit_observed_adapter")
    adapter_programs = {mode: adapter.program({"selection_mode": mode}) if adapter else independent.racket(mode)
                        for mode in independent.MODES}
    for mode, program in adapter_programs.items():
        if type(program) is not str or not program.strip():
            raise ValueError(f"Adapter returned an invalid program for {mode}")
    canonical_bytes = (HERE / "canonical.rkt").read_bytes()
    report["program_sha256"] = {mode: _sha(program.encode()) for mode, program in adapter_programs.items()}
    if adapter_programs["all_matches"].encode() != canonical_bytes:
        fail("default_program_not_exact_canonical")

    prediction_cache = {}

    def predict(mode, name, grid):
        key = (mode, name, _grid_id(grid))
        if key not in prediction_cache:
            try:
                fn = independent.intended if name is None else independent.bank(mode)[name]
                output = fn(grid, mode) if name is None else fn(grid)
                if not _output_grid(output):
                    raise ValueError("prediction is not an exact integer grid")
                prediction_cache[key] = (True, output)
            except Exception as error:
                prediction_cache[key] = (False, f"{type(error).__name__}: {error}")
        ok, value = prediction_cache[key]
        if not ok:
            raise RuntimeError(value)
        return value

    with protected_local_imports(runtime, HERE):
        apply, identity, bridge = _real_evaluator(runtime)
        report["racket"] = identity
        evaluated = {}

        def protected(program, grid, expected, *, mode, case, group):
            key = (_sha(program.encode()), _grid_id(grid))
            if key not in evaluated:
                try:
                    actual = apply(program, copy.deepcopy(grid))
                    evaluated[key] = (True, actual)
                except Exception as error:
                    evaluated[key] = (False, f"{type(error).__name__}: {error}")
                counts["protected_evaluations"] += 1
                counts["protected_" + group] += 1
            ok, actual = evaluated[key]
            if not ok:
                fail("protected_execution_error", mode=mode, case=case, group=group, error=actual)
            elif not _output_grid(actual) or actual != expected:
                fail("protected_label_mismatch", mode=mode, case=case, group=group,
                     input=grid, expected=expected, actual=actual)
            report["protected_labels"].append({
                "group": group, "case": case, "mode": mode, "program_sha256": key[0],
                "input_sha256": key[1], "input": grid,
                "output": actual if ok else None, "matches_independent_expected": ok and actual == expected,
            })
            return actual if ok else None

        try:
            if phase in {"fixtures", "all"}:
                canonical = canonical_pairs(TASK_ID, root=ROOT)
                for index, pair in enumerate(canonical):
                    expected = predict("all_matches", None, pair["input"])
                    if expected != pair["output"]:
                        fail("canonical_mirror_disagreement", index=index)
                    protected(adapter_programs["all_matches"], pair["input"], pair["output"],
                              mode="all_matches", case=f"canonical:{index}", group="canonical")
                counts["canonical_pairs"] = len(canonical)
                hand = independent.fixtures()
                for name, grid in hand.items():
                    report["fixtures"][name] = independent.feature_summary(grid)
                    for mode in independent.MODES:
                        expected = predict(mode, None, grid)
                        protected(adapter_programs[mode], grid, expected, mode=mode,
                                  case=name, group="hand")
                        reference = independent.racket(mode)
                        if reference != adapter_programs[mode]:
                            protected(reference, grid, expected, mode=mode,
                                      case=name + ":independent-program", group="independent_program")
                        for transform_name, transformed, output_transform in _transforms(grid):
                            target = output_transform(expected)
                            counts["metamorphic_python_cases"] += 1
                            if predict(mode, None, transformed) != target:
                                fail("metamorphic_python", mode=mode, case=name, transform=transform_name)
                            if name in {"unique_max_secondary_winner", "cross_color_aspect_tie",
                                        "private_rank_dominance", "maximum_30"}:
                                protected(adapter_programs[mode], transformed, target, mode=mode,
                                          case=name + ":" + transform_name, group="metamorphic")
                counts["hand_fixtures"] = len(hand)
                for mode in independent.MODES:
                    seen_signatures = {}
                    intended_signature = tuple(_encoded(predict(mode, None, grid)) for grid in hand.values())
                    for name in independent.bank(mode):
                        outputs = [predict(mode, name, grid) for grid in hand.values()]
                        signature = tuple(map(_encoded, outputs))
                        if signature == intended_signature:
                            fail("rival_not_distinguished", mode=mode, name=name)
                            continue
                        if signature in seen_signatures:
                            fail("rival_fixture_alias", mode=mode, first=seen_signatures[signature], second=name)
                        seen_signatures[signature] = name
                        witness_name, witness_grid = next((fixture_name, grid) for fixture_name, grid in hand.items()
                                                         if predict(mode, name, grid) != predict(mode, None, grid))
                        protected(independent.racket(mode, name), witness_grid, predict(mode, name, witness_grid),
                                  mode=mode, case=name + ":" + witness_name, group="rival_program")

            if phase in {"episodes", "all"}:
                contract = json.loads((HERE / "promotion.json").read_text(encoding="utf-8"))
                demo_low, demo_high = contract["limits"]["demos"]
                query_low, query_high = contract["limits"]["queries"]
                if not (3 <= demo_low <= demo_high <= 6 and 1 <= query_low <= query_high == 4):
                    raise ValueError("Audit expects the declared 3..6 demo /1..4 query family")
                report["supported_counts"] = {"demos": [demo_low, demo_high], "queries": [query_low, query_high]}
                matched_inputs, count_prefixes = {}, {}
                surviving_counts, ambiguity_families = Counter(), Counter()
                query_features_seen, demo_features_seen, generated_features = set(), set(), {}
                for seed in seeds:
                    for demos in range(demo_low, demo_high + 1):
                        for queries in range(query_low, query_high + 1):
                            for mode in independent.MODES:
                                case = f"seed={seed},demos={demos},queries={queries},mode={mode}"
                                episode = adapter.generate(seed, {"selection_mode": mode}, demos, queries)
                                counts["episodes"] += 1
                                if type(episode) is not dict or episode.get("program_solution") != adapter_programs[mode]:
                                    fail("episode_program", case=case)
                                    continue
                                train, test = episode.get("train"), episode.get("test")
                                if type(train) is not list or type(test) is not list or len(train) != demos or len(test) != queries:
                                    fail("episode_counts", case=case)
                                    continue
                                pairs, ids = train + test, []
                                valid = True
                                for index, pair in enumerate(pairs):
                                    if type(pair) is not dict or not {"input", "output"} <= pair.keys():
                                        fail("episode_pair_shape", case=case, index=index)
                                        valid = False
                                        continue
                                    try:
                                        independent.validate(pair["input"])
                                    except ValueError as error:
                                        fail("episode_input_grammar", case=case, index=index, message=str(error))
                                        valid = False
                                        continue
                                    if not _output_grid(pair["output"]):
                                        fail("episode_output_grammar", case=case, index=index)
                                        valid = False
                                        continue
                                    expected = predict(mode, None, pair["input"])
                                    counts["claimed_labels"] += 1
                                    ids.append(_grid_id(pair["input"]))
                                    if ids[-1] not in generated_features:
                                        generated_features[ids[-1]] = independent.feature_summary(pair["input"])
                                    if pair["output"] != expected:
                                        fail("episode_label_mismatch", case=case, index=index,
                                             input=pair["input"], expected=expected, actual=pair["output"])
                                if not valid:
                                    continue
                                if len(ids) != len(set(ids)):
                                    fail("episode_duplicate_inputs", case=case)
                                paired_key = (seed, demos, queries)
                                if paired_key in matched_inputs and matched_inputs[paired_key] != ids:
                                    fail("settings_change_input_stream", case=case)
                                matched_inputs[paired_key] = ids
                                for split_name, split_ids in (("train", ids[:demos]), ("test", ids[demos:])):
                                    key = (seed, mode, split_name)
                                    previous = count_prefixes.get(key, [])
                                    common = min(len(previous), len(split_ids))
                                    if previous[:common] != split_ids[:common]:
                                        fail("count_prefix_dependence", case=case, split=split_name)
                                    if len(split_ids) > len(previous):
                                        count_prefixes[key] = split_ids
                                survivors = [other for other in independent.MODES
                                             if all(predict(other, None, pair["input"]) == pair["output"] for pair in train)]
                                if survivors != [mode]:
                                    fail("finite_setting_ambiguity", case=case, survivors=survivors)
                                for name in independent.bank(mode):
                                    try:
                                        fitted = all(predict(mode, name, pair["input"]) == pair["output"] for pair in train)
                                        if not fitted:
                                            continue
                                        bad = [index for index, pair in enumerate(test)
                                               if predict(mode, name, pair["input"]) != pair["output"]]
                                    except Exception as error:
                                        fail("rival_execution_error", case=case, name=name, error=str(error))
                                        continue
                                    if not bad:
                                        surviving_counts[mode + ":" + name] += 1
                                        continue
                                    key = mode + ":" + name
                                    ambiguity_families[key] += 1
                                    report["ambiguity_count"] += 1
                                    if key not in report["first_ambiguity_per_rival"]:
                                        index = bad[0]
                                        pair = test[index]
                                        report["first_ambiguity_per_rival"][key] = {
                                            "case": case, "train": train, "query_index": index,
                                            "query": pair, "rival_output": predict(mode, name, pair["input"]),
                                            "note": "Actual complete demonstration set and actual generated query; no query answer used to filter demonstrations.",
                                        }
                                representative = seed in {seeds[0], seeds[-1]} and demos in {demo_low, demo_high} and queries == 4
                                if representative:
                                    for index, pair in enumerate(pairs):
                                        protected(adapter_programs[mode], pair["input"], predict(mode, None, pair["input"]),
                                                  mode=mode, case=case + f":pair={index}", group="generated")
                                    opposite = independent.MODES[1 - independent.MODES.index(mode)]
                                    alternate_outputs = [protected(adapter_programs[opposite], pair["input"],
                                                                  predict(opposite, None, pair["input"]), mode=opposite,
                                                                  case=case + f":alternate-demo={index}", group="alternate_setting")
                                                         for index, pair in enumerate(train)]
                                    if all(output == pair["output"] for output, pair in zip(alternate_outputs, train)):
                                        fail("protected_finite_setting_ambiguity", case=case)
                                if queries == 4:
                                    shapes = [independent.feature_summary(pair["input"])["input_shape"] for pair in test]
                                    if [30, 30] not in shapes:
                                        fail("missing_30x30_query", case=case, shapes=shapes)
                                if demos == demo_low and queries == 4:
                                    for index, pair in enumerate(train):
                                        grid_id = _grid_id(pair["input"])
                                        if grid_id not in demo_features_seen:
                                            demo_features_seen.add(grid_id)
                                            report["demonstration_features"].append({"seed": seed, "demo_index": index,
                                                                                    "input_sha256": grid_id,
                                                                                    **generated_features[grid_id]})
                                    for index, pair in enumerate(test):
                                        grid_id = _grid_id(pair["input"])
                                        if grid_id not in query_features_seen:
                                            query_features_seen.add(grid_id)
                                            report["query_features"].append({"seed": seed, "query_index": index,
                                                                            "input_sha256": grid_id,
                                                                            **generated_features[grid_id]})
                report["ambiguity_families"] = dict(sorted(ambiguity_families.items()))
                report["surviving_rivals_without_query_disagreement"] = dict(sorted(surviving_counts.items()))
                counts["distinct_generated_inputs"] = len({item for values in matched_inputs.values() for item in values})
                all_features = list(generated_features.values())
                report["generated_coverage"] = {
                    "colors_seen": sorted({value for feature in all_features for value in feature["palette"]}),
                    "distinct_palettes": len({tuple(feature["palette"]) for feature in all_features}),
                    "input_shapes": sorted({tuple(feature["input_shape"]) for feature in all_features}),
                    "row_private_numeric_ranks": sorted({rank for feature in all_features for rank in feature["row_private_numeric_ranks"]}),
                    "col_private_numeric_ranks": sorted({rank for feature in all_features for rank in feature["col_private_numeric_ranks"]}),
                    "maximum_header_nonzero_cells": max(feature["nonzero_header_cells"] for feature in all_features),
                    "maximum_equality_nonzero_cells": max(feature["equality_nonzero_cells"] for feature in all_features),
                    "maximum_equality_component_count": max(feature["equality_component_count"] for feature in all_features),
                    "maximum_retained_nonzero_cells": max(feature["retained_nonzero_cells"] for feature in all_features),
                }
        finally:
            bridge.close()

    after = _bindings()
    report["source_bindings_after"] = after
    report["source_unchanged"] = before == after
    if before != after:
        fail("source_drift_during_audit")
    report["failure_counts"] = dict(sorted(failure_counts.items()))
    report["counts"] = dict(sorted(counts.items()))
    report["passed"] = not failure_counts and report["ambiguity_count"] == 0
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--phase", choices=("fixtures", "episodes", "all"), default="all")
    parser.add_argument("--seeds", nargs="+", type=int, default=list(DEFAULT_SEEDS))
    args = parser.parse_args(argv)
    if not 1 <= len(args.seeds) <= 8 or len(set(args.seeds)) != len(args.seeds) or any(seed < 0 for seed in args.seeds):
        parser.error("Use one to eight distinct nonnegative seeds")
    if args.out.exists():
        parser.error("Choose a new report path; existing evidence is never overwritten")
    report = run(args.phase, tuple(args.seeds))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    print(json.dumps({"out": str(args.out), "passed": report["passed"],
                      "counts": report["counts"], "ambiguity_count": report["ambiguity_count"],
                      "failure_counts": report["failure_counts"], "source_unchanged": report["source_unchanged"]}, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
