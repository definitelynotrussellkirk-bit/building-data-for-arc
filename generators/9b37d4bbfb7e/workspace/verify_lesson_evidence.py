#!/usr/bin/env python3
"""Join two v1 census reports into a bounded evidence receipt, using only stdlib.

The generator is parsed, never executed. Report labels and rival scoring are
not rerun: this checks bindings, internal consistency, and complete recorded
coverage. It neither grants approval nor clears the shared semantic-gate warning.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import sys

SCHEMA = "arcpuzzles-lesson-census-v1"
RECEIPT_SCHEMA = "arcpuzzles-lesson-evidence-receipt-v1"
ZERO_COUNTS = ("materialization_errors", "ambiguous", "hook_warnings", "scoring_errors",
               "ambiguous_rotations", "rotation_hook_warnings", "rotation_scoring_errors")
GATE_WARNING = {
    "warning": "declared_period_not_enumerated", "resolved": False,
    "scope": "The shared semantic-gate warning remains unresolved; this receipt does not change or waive that gate.",
}


class EvidenceError(ValueError):
    """Evidence is absent, stale, inconsistent, or outside the supported contract."""


def require(condition, path, message):
    if not condition:
        raise EvidenceError(f"{path}: {message}")


def equal(value, expected, path):
    require(type(value) is type(expected) and value == expected, path,
            f"expected {expected!r}, got {value!r}")
    # Python container equality alone treats True as 1 and False as 0.
    # Evidence counters and recorded indices retain their JSON scalar types.
    if type(expected) is list:
        for index, item in enumerate(expected):
            equal(value[index], item, f"{path}[{index}]")
    elif type(expected) is dict:
        for key, item in expected.items():
            equal(value[key], item, f"{path}.{key}")


def object_at(value, path):
    require(type(value) is dict, path, "expected an object")
    return value


def list_at(value, path):
    require(type(value) is list, path, "expected a list")
    return value


def integer(value, path, minimum=0):
    require(type(value) is int and value >= minimum, path, f"expected an integer >= {minimum}")
    return value


def strings(value, path):
    result = list_at(value, path)
    require(result and all(type(x) is str and x for x in result), path, "expected nonempty strings")
    require(len(set(result)) == len(result), path, "duplicate entries")
    return result


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def sha(value, path):
    require(type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value), path, "expected a lowercase SHA-256")
    return value


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "JSON", f"duplicate key {key!r}")
        result[key] = value
    return result


def read_report(path):
    raw = path.read_bytes()
    def reject_constant(value):
        raise EvidenceError(f"JSON: invalid numeric constant {value}")
    report = json.loads(raw, object_pairs_hook=_unique_object, parse_constant=reject_constant)
    return object_at(report, str(path)), hashlib.sha256(raw).hexdigest()


def source_metadata(path):
    raw = path.read_bytes()
    wanted = {"GENERATOR_ID", "TASK_ID", "RULE_HASH", "LESSON_SCHEDULE_PERIOD", "EXAMPLES_NEEDED"}
    values = {}
    for node in ast.parse(raw, filename=str(path)).body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        names = [target.id for target in targets if isinstance(target, ast.Name) and target.id in wanted]
        if not names:
            continue
        try:
            value = values[node.value.id] if isinstance(node.value, ast.Name) else ast.literal_eval(node.value)
        except (ValueError, TypeError, KeyError) as exc:
            raise EvidenceError(f"generator metadata {names}: requires a literal or earlier metadata alias") from exc
        values.update(dict.fromkeys(names, value))
    require(wanted <= values.keys(), "generator metadata", f"missing {sorted(wanted - values.keys())}")
    require(type(values["TASK_ID"]) is str and values["TASK_ID"], "TASK_ID", "expected a nonempty string")
    equal(values["GENERATOR_ID"], values["TASK_ID"], "GENERATOR_ID")
    require(type(values["RULE_HASH"]) is str and re.fullmatch(r"[0-9a-f]{8,64}", values["RULE_HASH"]),
            "RULE_HASH", "expected a hexadecimal rule pin")
    integer(values["LESSON_SCHEDULE_PERIOD"], "LESSON_SCHEDULE_PERIOD", 1)
    integer(values["EXAMPLES_NEEDED"], "EXAMPLES_NEEDED", 1)
    values["generator_sha256"] = hashlib.sha256(raw).hexdigest()
    return values


def no_nested_issues(value, path, root=False):
    """Do not let detailed errors hide behind clean aggregate counters."""
    if type(value) is dict:
        for key, item in value.items():
            location = f"{path}.{key}"
            if key == "errors" or (key == "warnings" and not root):
                equal(item, [], location)
            elif key in ZERO_COUNTS:
                if key == "ambiguous" and type(item) is bool:
                    equal(item, False, location)
                else:
                    equal(item, 0, location)
            no_nested_issues(item, location)
    elif type(value) is list:
        for index, item in enumerate(value):
            no_nested_issues(item, f"{path}[{index}]")


def score_record(record, rivals, path):
    record = object_at(record, path)
    equal(record.get("contract"), "rivals", f"{path}.contract")
    equal(record.get("ambiguous"), False, f"{path}.ambiguous")
    for key in ("errors", "warnings"):
        equal(record.get(key), [], f"{path}.{key}")
    outcomes = object_at(record.get("rivals"), f"{path}.rivals")
    require(set(outcomes) == set(rivals), f"{path}.rivals", "must score exactly the declared rival set")
    for name, outcome in outcomes.items():
        equal(outcome, "refuted", f"{path}.rivals[{name}]")
    searched = object_at(record.get("searched_rivals"), f"{path}.searched_rivals")
    equal(searched.get("errors"), [], f"{path}.searched_rivals.errors")
    equal(searched.get("ambiguous"), False, f"{path}.searched_rivals.ambiguous")
    equal(searched.get("truncated"), False, f"{path}.searched_rivals.truncated")
    for name, candidate in object_at(searched.get("candidates"), f"{path}.searched_rivals.candidates").items():
        candidate = object_at(candidate, f"{path}.searched_rivals[{name}]")
        equal(candidate.get("status"), "refuted", f"{path}.searched_rivals[{name}].status")


def grid_hash(grid, path):
    rows = list_at(grid, path)
    require(rows and type(rows[0]) is list and rows[0], path, "expected a nonempty grid")
    width = len(rows[0])
    require(all(type(row) is list and len(row) == width for row in rows), path, "ragged grid")
    require(all(type(v) is int and 0 <= v <= 9 for row in rows for v in row), path, "invalid grid colors")
    return digest(rows)


def validate_report(report, metadata, schedule, path):
    task, source_hash = metadata["TASK_ID"], metadata["generator_sha256"]
    period, demos = metadata["LESSON_SCHEDULE_PERIOD"], metadata["EXAMPLES_NEEDED"]
    equal(report.get("schema"), SCHEMA, f"{path}.schema")
    for key, expected in (("task_id", task), ("rule_task_id", task), ("generator_sha256", source_hash),
                          ("declared_rule_hash", metadata["RULE_HASH"]), ("declared_schedule_period", period),
                          ("contract", "rivals"), ("rotation_policy", "require")):
        equal(report.get(key), expected, f"{path}.{key}")
    for key in ("status", "production_status", "rotation_status"):
        equal(report.get(key), "no_ambiguity_found", f"{path}.{key}")
    for key in ("rule_source_sha256", "rule_callable_sha256"):
        sha(report.get(key), f"{path}.{key}")
    require(type(report.get("rule_file")) is str and report["rule_file"], f"{path}.rule_file", "missing rule file")
    equal(report.get("errors"), [], f"{path}.errors")
    warnings = list_at(report.get("warnings"), f"{path}.warnings")
    allowed = [] if schedule else ["Declared short schedule was not explicitly enumerated"]
    require(all(item in allowed for item in warnings), f"{path}.warnings", "unrecognized warning")
    no_nested_issues(report, path, root=True)
    execution = object_at(report.get("execution"), f"{path}.execution")
    equal(execution.get("exit_code"), 0, f"{path}.execution.exit_code")
    equal(execution.get("timed_out"), False, f"{path}.execution.timed_out")
    equal(report.get("materializer_rejection_logs"), {}, f"{path}.materializer_rejection_logs")
    catalog = object_at(report.get("catalog_provenance"), f"{path}.catalog_provenance")
    equal(catalog.get("rule_hash"), metadata["RULE_HASH"], f"{path}.catalog_provenance.rule_hash")

    sampler = object_at(report.get("sampler"), f"{path}.sampler")
    for key, expected in (("task_id", task), ("n_demos", demos), ("n_queries", 1),
                          ("rotate_query", True), ("rotation_policy", "require"),
                          ("enumerate_schedule_period", schedule)):
        equal(sampler.get(key), expected, f"{path}.sampler.{key}")
    bands = strings(sampler.get("bands"), f"{path}.sampler.bands")
    count_per_band = integer(sampler.get("per_band"), f"{path}.sampler.per_band", 1)
    bundle_size = demos + 1
    rivals = strings(report.get("rivals"), f"{path}.rivals")

    manifest = object_at(report.get("runtime_manifest"), f"{path}.runtime_manifest")
    equal(manifest.get("task_id"), task, f"{path}.runtime_manifest.task_id")
    files = list_at(manifest.get("files"), f"{path}.runtime_manifest.files")
    bound_files = {}
    for expected in (f"puzzle_generators/per_puzzle/{task}/generator.py", report["rule_file"]):
        matches = [item for item in files if type(item) is dict and item.get("runtime_path") == expected]
        require(len(matches) == 1, f"{path}.runtime_manifest", f"expected exactly one entry for {expected}")
        bound_files[expected] = sha(matches[0].get("sha256"), f"{path}.runtime_manifest[{expected}].sha256")
    equal(bound_files[f"puzzle_generators/per_puzzle/{task}/generator.py"], source_hash,
          f"{path}.runtime_manifest.generator_sha256")

    lessons = list_at(report.get("lessons"), f"{path}.lessons")
    equal(len(lessons), len(bands) * count_per_band, f"{path}.lessons.count")
    seen, input_sets = set(), {band: set() for band in bands}
    for offset, lesson in enumerate(lessons):
        where = f"{path}.lessons[{offset}]"
        score_record(lesson, rivals, where)
        band = lesson.get("band")
        require(band in bands, f"{where}.band", "undeclared band")
        index = integer(lesson.get("index"), f"{where}.index")
        start = integer(lesson.get("sample_index"), f"{where}.sample_index")
        equal(start, index, f"{where}.sample_index")
        require(index < count_per_band and (band, index) not in seen, where, "missing or duplicate band/start index")
        seen.add((band, index))
        seed = integer(lesson.get("seed"), f"{where}.seed")
        if schedule:
            equal(seed, sampler.get("schedule_seed"), f"{where}.seed")
        instance = object_at(lesson.get("instance"), f"{where}.instance")
        equal(sha(lesson.get("instance_sha256"), f"{where}.instance_sha256"), digest(instance), f"{where}.instance_sha256")
        for key, expected in (("task_id", task), ("rule_task_id", task), ("rule_file", report["rule_file"]),
                              ("seed", seed), ("sample_index", start)):
            equal(instance.get(key), expected, f"{where}.instance.{key}")
        training = list_at(instance.get("train"), f"{where}.instance.train")
        queries = list_at(instance.get("test"), f"{where}.instance.test")
        equal(len(training), demos, f"{where}.instance.train.count")
        equal(len(queries), 1, f"{where}.instance.test.count")
        hashes = []
        for j, pair in enumerate(training + queries):
            pair = object_at(pair, f"{where}.pairs[{j}]")
            hashes.append(grid_hash(pair.get("input"), f"{where}.pairs[{j}].input"))
            grid_hash(pair.get("output"), f"{where}.pairs[{j}].output")
        input_sets[band].update(hashes)
        sampling = object_at(instance.get("sampling"), f"{where}.sampling")
        for key, expected in (("schema", "arcpuzzles-pair-sampling-v1"), ("requested_start", start),
                              ("next_sample_index", start + bundle_size), ("attempted_pairs", bundle_size), ("rejections", [])):
            equal(sampling.get(key), expected, f"{where}.sampling.{key}")
        accepted = list_at(sampling.get("accepted_pairs"), f"{where}.sampling.accepted_pairs")
        equal(len(accepted), bundle_size, f"{where}.sampling.accepted_pairs.count")
        for j, pair in enumerate(accepted):
            pair = object_at(pair, f"{where}.sampling.accepted_pairs[{j}]")
            for key, expected in (("split", "train" if j < demos else "test"),
                                  ("pair_index", j if j < demos else 0), ("sample_index", start + j),
                                  ("input_sha256", hashes[j])):
                equal(pair.get(key), expected, f"{where}.sampling.accepted_pairs[{j}].{key}")
        rotations = list_at(lesson.get("rotations"), f"{where}.rotations")
        equal(len(rotations), bundle_size, f"{where}.rotations.count")
        query_indices = set()
        for j, rotation in enumerate(rotations):
            location = f"{where}.rotations[{j}]"
            score_record(rotation, rivals, location)
            query = integer(rotation.get("query_index"), f"{location}.query_index")
            require(query < bundle_size and query not in query_indices, f"{location}.query_index", "missing or duplicate query position")
            query_indices.add(query)
            equal(rotation.get("train_indices"), [i for i in range(bundle_size) if i != query], f"{location}.train_indices")

    per_band = object_at(report.get("per_band"), f"{path}.per_band")
    require(set(per_band) == set(bands), f"{path}.per_band", "must contain every declared band exactly once")
    totals = {"requested": len(lessons), "materialized": len(lessons),
              "pairs": len(lessons) * bundle_size, "rotations": len(lessons) * bundle_size}
    summary = object_at(report.get("summary"), f"{path}.summary")
    for name, stats, multiplier in [("summary", summary, len(bands))] + [
            (f"per_band[{band}]", object_at(per_band[band], f"{path}.per_band[{band}]"), 1) for band in bands]:
        for key in ZERO_COUNTS:
            equal(stats.get(key), 0, f"{path}.{name}.{key}")
        for key in ("requested", "materialized", "pairs", "rotations"):
            expected = count_per_band * multiplier * (bundle_size if key in ("pairs", "rotations") else 1)
            equal(stats.get(key), expected, f"{path}.{name}.{key}")
    for band, stats in per_band.items():
        equal(stats.get("rivals"), {name: {"refuted": count_per_band} for name in rivals}, f"{path}.per_band[{band}].rivals")
        if "unique_inputs" in stats:
            equal(stats["unique_inputs"], len(input_sets[band]), f"{path}.per_band[{band}].unique_inputs")
    unique = len(set().union(*input_sets.values()))
    for name, stats in (("summary", summary), ("report", report)):
        if "unique_inputs" in stats:
            equal(stats["unique_inputs"], unique, f"{path}.{name}.unique_inputs")

    if schedule:
        equal(count_per_band, period, f"{path}.sampler.per_band")
        equal(report.get("enumerated_schedule_period"), period, f"{path}.enumerated_schedule_period")
        seed = integer(sampler.get("schedule_seed"), f"{path}.sampler.schedule_seed")
        coverage = object_at(report.get("schedule_coverage"), f"{path}.schedule_coverage")
        for key, expected in (("status", "complete_fixed_seed"), ("contract", "LESSON_SCHEDULE_PERIOD"),
                              ("period", period), ("seed", seed), ("generator_sha256", source_hash),
                              ("rule_source_sha256", report["rule_source_sha256"]),
                              ("expected_lessons", totals["materialized"]), ("expected_rotations", totals["rotations"])):
            equal(coverage.get(key), expected, f"{path}.schedule_coverage.{key}")
        require(set(strings(coverage.get("bands"), f"{path}.schedule_coverage.bands")) == set(bands),
                f"{path}.schedule_coverage.bands", "does not cover all declared bands")
    else:
        equal(report.get("enumerated_schedule_period"), None, f"{path}.enumerated_schedule_period")
    return {"lessons": len(lessons), "pairs": totals["pairs"], "rotations": totals["rotations"],
            "unique_inputs": unique, "bands": bands, "rivals": rivals, "warnings": warnings,
            "rule_record_sha256": bound_files[report["rule_file"]]}


def verify(generator, random_path, schedule_path):
    metadata = source_metadata(generator)
    random, random_hash = read_report(random_path)
    schedule, schedule_hash = read_report(schedule_path)
    for key in ("task_id", "generator_sha256", "rule_task_id", "rule_file", "declared_rule_hash",
                "rule_source_sha256", "rule_callable_sha256"):
        equal(schedule.get(key), random.get(key), f"report binding.{key}")
    random_info = validate_report(random, metadata, False, "random_census")
    schedule_info = validate_report(schedule, metadata, True, "schedule_census")
    for key in ("bands", "rivals"):
        require(set(random_info[key]) == set(schedule_info[key]), f"report binding.{key}", "report declarations differ")
    equal(schedule_info["rule_record_sha256"], random_info["rule_record_sha256"], "report binding.rule_record_sha256")
    counts = lambda info: {key: info[key] for key in ("lessons", "pairs", "rotations", "unique_inputs")}
    return {
        "schema": RECEIPT_SCHEMA, "status": "evidence_verified", "task_id": metadata["TASK_ID"],
        "generator_sha256": metadata["generator_sha256"], "declared_rule_hash": metadata["RULE_HASH"],
        "rule_source_sha256": random["rule_source_sha256"], "rule_callable_sha256": random["rule_callable_sha256"],
        "rule_record_sha256": random_info["rule_record_sha256"], "rival_count": len(random_info["rivals"]),
        "bands": random_info["bands"], "n_demos": metadata["EXAMPLES_NEEDED"], "n_queries": 1,
        "rotation_policy": "require", "global_approval": False, "shared_semantic_gate": GATE_WARNING,
        "random_census": {**counts(random_info), "path": str(random_path), "sha256": random_hash,
                          "warnings": random_info["warnings"]},
        "schedule_census": {**counts(schedule_info), "path": str(schedule_path), "sha256": schedule_hash,
                            "period": metadata["LESSON_SCHEDULE_PERIOD"], "seed": schedule["sampler"]["schedule_seed"],
                            "start_residues": list(range(metadata["LESSON_SCHEDULE_PERIOD"])),
                            "query_positions": list(range(metadata["EXAMPLES_NEEDED"] + 1))},
        "limits": [
            "Finite report-consistency and declared-rival evidence, not proof of identifiability or global approval.",
            "Labels and rival predictions are trusted report evidence; this CLI does not execute Racket or rerun scoring.",
            "Rule source and callable hashes are cross-report bindings; this CLI does not independently rehash the Racket artifacts.",
            "Schedule completeness covers this fixed seed, declared bands, starting residues, and recorded query positions only.",
            "The period is a generator declaration, not an independently proven bound on random behavior.",
            "All reported rival scores must be refuted; unlisted rival programs and other seeds are outside this receipt.",
            "The shared semantic-gate warning remains unresolved; no catalog, approval, or training-admission state changes.",
        ],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path, default=Path(__file__).resolve().parents[1] / "generator.py")
    parser.add_argument("--random-census", type=Path, required=True)
    parser.add_argument("--schedule-census", type=Path, required=True)
    parser.add_argument("--output", type=Path, help="Optional JSON receipt; failures replace it with a rejection receipt.")
    args = parser.parse_args(argv)
    output_safe = args.output is None or args.output.resolve() not in {
        args.generator.resolve(), args.random_census.resolve(), args.schedule_census.resolve()}
    try:
        require(output_safe, "--output", "must not overwrite a source or census input")
        result = verify(args.generator, args.random_census, args.schedule_census)
        exit_code = 0
    except (EvidenceError, OSError, ValueError, SyntaxError, TypeError, KeyError) as exc:
        result = {"schema": RECEIPT_SCHEMA, "status": "rejected", "error": str(exc),
                  "global_approval": False, "shared_semantic_gate": GATE_WARNING}
        exit_code = 1
    encoded = json.dumps(result, indent=2) + "\n"
    if args.output is not None and output_safe:
        try:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(encoded)
        except OSError as exc:
            result = {"schema": RECEIPT_SCHEMA, "status": "rejected", "error": f"--output: {exc}",
                      "global_approval": False, "shared_semantic_gate": GATE_WARNING}
            encoded, exit_code = json.dumps(result, indent=2) + "\n", 1
    sys.stdout.write(encoded)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
