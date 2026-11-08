#!/usr/bin/env python3
"""Re-score a retained public lesson census without invoking Racket authority.

Run through the packet's run_with_racket.py wrapper so imports resolve to that
packet's own runtime. Supply --generator explicitly; its bytes must match the
census before any generator code is imported. Both .json and .json.gz work.

The census embeds generated Racket-labelled pairs, but only a canonical-pair
count and fit summary. Canonical inputs/labels therefore come from the public
reviewer_support helper in the selected generator's own tree. The entire local
canonical ledger must match its hash in the retained census runtime manifest.

Exit codes: 0 = completed with no measured ambiguity, 1 = measured ambiguity,
2 = malformed evidence, source mismatch, failed canonical claim, or scoring
error. A rival agreeing everywhere is survived_all, not ambiguity. Output paths
must be new; existing evidence is never overwritten.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


SCHEMA = "arcpuzzles-rival-certificate-v1"
LABEL_BASIS = (
    "Reuses saved public Racket labels from the source-bound lesson census; "
    "this tool does not invoke Racket authority or generate new labels."
)
NAMESPACES = ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS")
COMPLETE_STATUSES = {
    "no_ambiguity_found", "ambiguous", "warning", "hook_only", "no_contract",
}


class CertificateError(Exception):
    def __init__(self, code, message, **context):
        super().__init__(message)
        self.detail = {"code": code, "message": message, **context}


def require(condition, message, *, code="malformed_census", **context):
    if not condition:
        raise CertificateError(code, message, **context)


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def file_digest(path):
    result = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def valid_hash(value):
    return (isinstance(value, str) and len(value) == 64
            and all(char in "0123456789abcdef" for char in value))


def valid_grid(grid):
    return (isinstance(grid, list) and bool(grid)
            and isinstance(grid[0], list) and bool(grid[0])
            and all(isinstance(row, list) and len(row) == len(grid[0])
                    and all(type(value) is int and 0 <= value <= 9 for value in row)
                    for row in grid))


def read_census(path):
    raw = path.read_bytes()
    decoded = gzip.decompress(raw) if raw.startswith(b"\x1f\x8b") else raw
    value = json.loads(decoded)
    require(isinstance(value, dict), "Expected a census JSON object")
    return value, hashlib.sha256(raw).hexdigest()


def validate_census(census):
    """Validate retained labels, completion, identities and accepted indices."""
    require(census.get("schema") == "arcpuzzles-lesson-census-v1",
            "Unsupported public census schema")
    task = census.get("task_id")
    require(isinstance(task, str) and task and task.isalnum(), "Invalid task id")
    for field in ("generator_sha256", "rule_source_sha256", "rule_callable_sha256"):
        require(valid_hash(census.get(field)), f"Invalid {field}")
    for field in ("status", "production_status"):
        require(census.get(field) in COMPLETE_STATUSES,
                f"Retained {field} is incomplete or errored")
    require(census.get("rotation_status") in COMPLETE_STATUSES | {"not_requested"},
            "Retained rotation status is incomplete or errored")
    require(census.get("errors") == [], "Retained census contains errors")
    execution = census["execution"]
    expected_exit = 1 if census["status"] == "ambiguous" else 0
    require(execution.get("timed_out") is False
            and type(execution.get("exit_code")) is int
            and execution["exit_code"] == expected_exit,
            "Retained census execution did not complete")
    manifest = census["runtime_manifest"]
    manifest_hash = hashlib.sha256(
        (json.dumps(manifest, indent=2) + "\n").encode()
    ).hexdigest()
    require(manifest_hash == census["runtime_manifest_sha256"],
            "Retained runtime manifest hash mismatch")
    require(manifest.get("task_id") == task, "Runtime manifest task mismatch")
    source_entries = [row for row in manifest["files"]
                      if row.get("library_path") == f"generators/{task}/generator.py"]
    require(len(source_entries) == 1
            and source_entries[0].get("sha256") == census["generator_sha256"],
            "Generator source is not bound to the retained manifest")
    lessons, summary, sampler = census["lessons"], census["summary"], census["sampler"]
    require(isinstance(lessons, list) and lessons, "Retained census has no lessons")
    require(type(summary.get("requested")) is int and summary["requested"] > 0
            and summary["requested"] == summary.get("materialized") == len(lessons),
            "Incomplete or inconsistent retained lesson population")
    for field in ("materialization_errors", "scoring_errors", "rotation_scoring_errors"):
        require(type(summary.get(field)) is int and summary[field] == 0,
                f"Retained census reports {field}")
    require(type(sampler.get("n_demos")) is int and sampler["n_demos"] > 0
            and type(sampler.get("n_queries")) is int and sampler["n_queries"] == 1,
            "This certificate requires demonstrations and exactly one production query")
    require(type(sampler.get("rotate_query")) is bool,
            "Missing or invalid retained rotation setting")
    identities, by_band, flattened = set(), Counter(), []
    pair_total = retained_rotation_total = 0
    for position, lesson in enumerate(lessons):
        require(isinstance(lesson, dict) and lesson.get("errors") == [],
                "Malformed or errored retained lesson", lesson_position=position)
        band, index = lesson["band"], lesson["index"]
        require(isinstance(band, str) and type(index) is int and index >= 0,
                "Invalid retained lesson identity")
        require((band, index) not in identities, "Duplicate retained lesson identity")
        identities.add((band, index))
        by_band[band] += 1
        instance = lesson["instance"]
        require(digest(instance) == lesson["instance_sha256"],
                "Retained instance hash mismatch", band=band, lesson_index=index)
        require(instance.get("task_id") == task
                and instance.get("rule_task_id") == census["rule_task_id"]
                and instance.get("rule_file") == census["rule_file"],
                "Retained instance rule binding mismatch")
        require(type(lesson.get("seed")) is int
                and lesson["seed"] == instance.get("seed"), "Retained seed mismatch")
        train, tests = instance["train"], instance["test"]
        tests = tests if isinstance(tests, list) else [tests]
        require(isinstance(train, list) and len(train) == sampler["n_demos"]
                and len(tests) == 1, "Retained lesson has an incomplete split")
        sampling = instance["sampling"]
        require(sampling.get("schema") == "arcpuzzles-pair-sampling-v1",
                "Missing accepted-pair sampling metadata; indices are never inferred")
        requested = lesson["sample_index"]
        require(type(requested) is int and requested >= 0
                and requested == instance.get("sample_index") == sampling.get("requested_start"),
                "Retained requested-start mismatch")
        accepted = sampling["accepted_pairs"]
        require(isinstance(accepted, list) and len(accepted) == len(train) + len(tests),
                "Incomplete accepted-pair metadata")
        accepted_by_pair, accepted_indices = {}, set()
        for entry in accepted:
            require(isinstance(entry, dict) and entry.get("split") in ("train", "test")
                    and type(entry.get("pair_index")) is int
                    and type(entry.get("sample_index")) is int,
                    "Malformed accepted-pair identity")
            key = (entry["split"], entry["pair_index"])
            require(key not in accepted_by_pair
                    and entry["sample_index"] not in accepted_indices
                    and entry["sample_index"] >= requested,
                    "Duplicate or invalid accepted-pair identity")
            accepted_by_pair[key] = entry
            accepted_indices.add(entry["sample_index"])
        records = []
        for split, pairs in (("train", train), ("test", tests)):
            for pair_index, pair in enumerate(pairs):
                require(isinstance(pair, dict) and valid_grid(pair.get("input"))
                        and valid_grid(pair.get("output")),
                        "Malformed retained input or Racket output")
                key = (split, pair_index)
                require(key in accepted_by_pair, "Accepted-pair metadata does not cover split")
                accepted_row = accepted_by_pair[key]
                require(accepted_row.get("input_sha256") == digest(pair["input"]),
                        "Accepted-pair input hash mismatch")
                records.append({"pair": pair, "accepted": accepted_row,
                                "split": split, "pair_index": pair_index})
        require(type(sampling.get("next_sample_index")) is int
                and sampling["next_sample_index"] > max(accepted_indices),
                "Invalid accepted-pair next index")
        rotations = lesson.get("rotations", [])
        expected_rotations = len(records) if sampler["rotate_query"] else 0
        require(isinstance(rotations, list) and len(rotations) == expected_rotations,
                "Incomplete retained query rotations")
        for query_index, rotation in enumerate(rotations):
            require(rotation.get("errors") == []
                    and rotation.get("query_index") == query_index
                    and rotation.get("train_indices") == [
                        i for i in range(len(records)) if i != query_index],
                    "Malformed or errored retained query rotation")
        pair_total += len(records)
        retained_rotation_total += len(rotations)
        flattened.append((lesson, records))
    require(summary.get("pairs") == pair_total
            and summary.get("rotations") == retained_rotation_total,
            "Retained pair or rotation totals disagree with evidence")
    require(set(census["per_band"]) == set(by_band)
            and set(sampler["bands"]) == set(by_band)
            and len(sampler["bands"]) == len(by_band), "Retained band coverage mismatch")
    require(type(sampler.get("per_band")) is int and sampler["per_band"] > 0,
            "Invalid retained per-band request")
    for band, count in by_band.items():
        require(count == sampler["per_band"]
                == census["per_band"][band].get("requested")
                == census["per_band"][band].get("materialized")
                and {i for b, i in identities if b == band} == set(range(count)),
                "Incomplete retained band population", band=band)
    return flattened


def load_generator(path, source, census):
    spec = importlib.util.spec_from_file_location("_rival_certificate_generator", path)
    require(spec is not None, "Cannot construct selected generator import", code="import_error")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    # Execute the hash-checked bytes, avoiding stale bytecode or a second read.
    exec(compile(source, str(path), "exec"), module.__dict__)
    require(module.GENERATOR_ID == module.TASK_ID == census["task_id"],
            "Selected generator identity mismatch", code="source_mismatch")
    require(module.RULE_HASH == census["declared_rule_hash"]
            and census["rule_source_sha256"].startswith(module.RULE_HASH),
            "Selected rule pin differs from retained authority", code="source_mismatch")
    require(all(row["instance"].get("generator_version") == module.VERSION
                for row in census["lessons"]),
            "Retained generator version mismatch", code="source_mismatch")
    return module


def canonical_evidence(generator_path, census):
    try:
        from reviewer_support import canonical_pairs, canonical_path, find_root
    except ImportError as error:
        raise CertificateError(
            "import_error", "Run this tool under the packet's run_with_racket.py wrapper"
        ) from error
    root = find_root(generator_path)
    ledger = canonical_path(root)
    entries = [row for row in census["runtime_manifest"]["files"]
               if row.get("runtime_path") == "data/canonical/puzzles.jsonl"]
    require(len(entries) == 1 and valid_hash(entries[0].get("sha256")),
            "Retained manifest does not bind one canonical ledger")
    actual_hash = file_digest(ledger)
    require(actual_hash == entries[0]["sha256"],
            "Local canonical ledger differs from the retained census ledger",
            code="source_mismatch", expected_sha256=entries[0]["sha256"],
            actual_sha256=actual_hash)
    pairs = canonical_pairs(census["task_id"], root=root, labeled_only=True)
    require(pairs and type(census.get("canonical_pairs")) is int
            and len(pairs) == census["canonical_pairs"],
            "Retained canonical-pair count disagrees with its bound ledger")
    return pairs, {
        "path": str(ledger), "sha256": actual_hash, "pairs": len(pairs),
        "binding": "Local public canonical ledger exactly matches census runtime-manifest bytes",
        "pair_identities": [
            {key: pair[key] for key in ("variant", "split", "pair_index")}
            for pair in pairs
        ],
        "selected_pairs_sha256": digest(pairs),
    }


def declarations(module):
    result = {}
    for namespace in NAMESPACES:
        declared = getattr(module, namespace, None)
        require(isinstance(declared, dict), f"{namespace} must be a dictionary",
                code="declaration_error")
        for name, fn in sorted(declared.items()):
            require(isinstance(name, str) and name and callable(fn),
                    f"Malformed entry in {namespace}", code="declaration_error")
            result[f"{namespace}:{name}"] = (namespace, name, fn)
    require(result, "No declared rivals to score", code="declaration_error")
    return result


def counterexample(lesson, record, rival_output):
    pair = record["pair"]
    return {
        "seed": lesson["seed"], "band": lesson["band"],
        "lesson_index": lesson["index"], "requested_start": lesson["sample_index"],
        "accepted_sample_index": record["accepted"]["sample_index"],
        "split": record["split"], "pair_index": record["pair_index"],
        "input": pair["input"], "retained_racket_output": pair["output"],
        "rival_output": rival_output,
        "hashes": {
            "instance_sha256": lesson["instance_sha256"],
            "input_sha256": record["accepted"]["input_sha256"],
            "retained_pair_sha256": digest(pair),
            "retained_racket_output_sha256": digest(pair["output"]),
            "rival_output_sha256": digest(rival_output),
        },
    }


def rescore(module, declared, canonical, lessons, report):
    prediction_cache = {}

    def predict(qualified, fn, grid, phase):
        key = (id(fn), digest(grid))
        if key not in prediction_cache:
            try:
                argument = deepcopy(grid)
                output = fn(argument)
                if argument != grid:
                    raise ValueError("Rival mutated its input")
                if not valid_grid(output):
                    raise ValueError("Rival returned a malformed grid")
                prediction_cache[key] = deepcopy(output)
            except Exception as error:
                raise CertificateError(
                    "scoring_error", "Declared rival could not be scored",
                    rival=qualified, phase=phase, input_sha256=key[1],
                    error_type=type(error).__name__, error=str(error),
                ) from error
        return prediction_cache[key]

    rows, claims_failed = {}, []
    for qualified, (namespace, name, fn) in declared.items():
        fits = sum(predict(qualified, fn, pair["input"], "canonical") == pair["output"]
                   for pair in canonical)
        claim = namespace == "CANONICAL_SHORTCUTS"
        rows[qualified] = {
            "namespace": namespace, "name": name, "claims_canonical_fit": claim,
            "canonical_pairs": len(canonical), "canonical_fits": fits,
            "generated_pairs": 0, "generated_refutations": 0,
            "generated_unique_inputs": 0, "generated_unique_refutations": 0,
            "production": Counter(), "every_holdout": Counter(), "per_band": {},
            "generated_counterexample": None,
        }
        if claim and fits != len(canonical):
            claims_failed.append({"rival": qualified, "pairs": len(canonical), "fits": fits})
    report["rivals"] = rows
    require(not claims_failed, "Claimed canonical shortcuts fail retained canonical labels",
            code="canonical_claim_failure", failed_claims=claims_failed)
    production_ambiguous, holdout_ambiguous = set(), set()
    unique_inputs, refuted_inputs = set(), {name: set() for name in declared}
    per_band, retained_comparisons = {}, 0
    for position, (lesson, records) in enumerate(lessons):
        band = lesson["band"]
        band_summary = per_band.setdefault(band, {
            "lessons": 0, "pairs": 0, "holdouts": 0,
            "production_ambiguous_lessons": 0, "ambiguous_holdouts": 0,
        })
        band_summary["lessons"] += 1
        band_summary["pairs"] += len(records)
        band_summary["holdouts"] += len(records)
        unique_inputs.update(record["accepted"]["input_sha256"] for record in records)
        for qualified, (_, _, fn) in declared.items():
            row = rows[qualified]
            local = row["per_band"].setdefault(band, {
                "generated_pairs": 0, "generated_refutations": 0,
                "production": Counter(), "every_holdout": Counter(),
            })
            outputs = [predict(qualified, fn, record["pair"]["input"], "generated")
                       for record in records]
            matches = [output == record["pair"]["output"]
                       for output, record in zip(outputs, records)]
            row["generated_pairs"] += len(records)
            local["generated_pairs"] += len(records)
            for record, output, agrees in zip(records, outputs, matches):
                if not agrees:
                    row["generated_refutations"] += 1
                    local["generated_refutations"] += 1
                    refuted_inputs[qualified].add(record["accepted"]["input_sha256"])
                    if row["generated_counterexample"] is None:
                        row["generated_counterexample"] = counterexample(lesson, record, output)
            train_count = len(lesson["instance"]["train"])
            production = ("refuted" if not all(matches[:train_count])
                          else "survived_all" if all(matches[train_count:]) else "ambiguous")
            row["production"][production] += 1
            local["production"][production] += 1
            if production == "ambiguous":
                production_ambiguous.add(position)
            saved_production = lesson.get("rivals", {}).get(qualified)
            if saved_production is not None:
                require(saved_production == production,
                        "Independent score differs from retained production score",
                        code="scoring_error", rival=qualified, seed=lesson["seed"], band=band)
                retained_comparisons += 1
            for held_out in range(len(records)):
                fits_demos = all(agrees for i, agrees in enumerate(matches) if i != held_out)
                status = ("refuted" if not fits_demos
                          else "survived_all" if matches[held_out] else "ambiguous")
                row["every_holdout"][status] += 1
                local["every_holdout"][status] += 1
                if status == "ambiguous":
                    holdout_ambiguous.add((position, held_out))
                if lesson.get("rotations"):
                    saved = lesson["rotations"][held_out].get("rivals", {}).get(qualified)
                    if saved is not None:
                        require(saved == status,
                                "Independent score differs from retained holdout score",
                                code="scoring_error", rival=qualified, seed=lesson["seed"],
                                band=band, held_out=held_out)
                        retained_comparisons += 1
    for qualified, row in rows.items():
        row["generated_unique_inputs"] = len(unique_inputs)
        row["generated_unique_refutations"] = len(refuted_inputs[qualified])
        for counts in (row["production"], row["every_holdout"]):
            for status in ("refuted", "survived_all", "ambiguous"):
                counts.setdefault(status, 0)
    for position in production_ambiguous:
        per_band[lessons[position][0]["band"]]["production_ambiguous_lessons"] += 1
    for position, _ in holdout_ambiguous:
        per_band[lessons[position][0]["band"]]["ambiguous_holdouts"] += 1
    report["summary"] = {
        "lessons": len(lessons), "generated_pairs": sum(len(records) for _, records in lessons),
        "unique_generated_inputs": len(unique_inputs),
        "holdouts_scored": sum(len(records) for _, records in lessons),
        "canonical_shortcut_claims": len(module.CANONICAL_SHORTCUTS),
        "lesson_competitors": len(module.LESSON_COMPETITORS),
        "declaration_entries": len(declared),
        "distinct_declared_names": len({name for _, name, _ in declared.values()}),
        "production_ambiguous_lessons": len(production_ambiguous),
        "ambiguous_holdouts": len(holdout_ambiguous),
        "retained_score_comparisons": retained_comparisons,
    }
    report["per_band"] = per_band
    report["production_status"] = "ambiguous" if production_ambiguous else "no_ambiguity_found"
    report["every_holdout_status"] = "ambiguous" if holdout_ambiguous else "no_ambiguity_found"
    return 1 if production_ambiguous or holdout_ambiguous else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--census", required=True, type=Path, help="Retained public .json or .json.gz census")
    parser.add_argument("--generator", required=True, type=Path, help="Explicit selected generator.py")
    parser.add_argument("--output", required=True, type=Path, help="New compact certificate JSON path")
    args = parser.parse_args(argv)
    args.census, args.generator, args.output = (
        path.resolve() for path in (args.census, args.generator, args.output)
    )
    report = {
        "schema": SCHEMA, "created_utc": datetime.now(timezone.utc).isoformat(),
        "label_basis": LABEL_BASIS, "authority_invoked": False,
        "generator_imported": False,
        "tool": {"path": str(Path(__file__).resolve()), "sha256": file_digest(Path(__file__))},
        "execution": {"argv": list(sys.orig_argv), "cwd": str(Path.cwd())},
        "census": {"path": str(args.census)}, "generator": {"path": str(args.generator)},
        "limits": [
            "Finite declared-rival evidence, not proof of identifiability or training admission.",
            "Every holdout reuses the retained labelled bundle; no new draw or authority call occurs.",
            "Rivals are assumed deterministic; cached predictions are checked for valid grids and input purity.",
            "Canonical labels are recovered from the exact ledger bound by the retained runtime manifest.",
        ],
        "errors": [],
    }
    exit_code = 2
    try:
        require(not args.output.exists(), "Output already exists; refusing to overwrite evidence",
                code="output_exists")
        census, census_hash = read_census(args.census)
        source = args.generator.read_bytes()
        source_hash = hashlib.sha256(source).hexdigest()
        report["census"].update({"sha256": census_hash, "json_sha256": digest(census),
                                  "generator_sha256": census.get("generator_sha256")})
        report["generator"]["sha256"] = source_hash
        require(census.get("generator_sha256") == source_hash,
                "Census generator_sha256 does not match supplied generator bytes",
                code="source_mismatch", expected_sha256=census.get("generator_sha256"),
                actual_sha256=source_hash)
        lessons = validate_census(census)
        module = load_generator(args.generator, source, census)
        report["generator_imported"] = True
        report["task_id"] = census["task_id"]
        report["generator"].update({"version": module.VERSION, "rule_hash": module.RULE_HASH})
        report["census"].update({key: census[key] for key in (
            "rule_source_sha256", "rule_callable_sha256", "runtime_manifest_sha256",
        )})
        report["retained_census_status"] = {
            key: census[key] for key in ("status", "production_status", "rotation_status")
        }
        canonical, binding = canonical_evidence(args.generator, census)
        report["canonical_ledger"] = binding
        declared = declarations(module)
        report["declarations"] = {
            namespace: sorted(getattr(module, namespace)) for namespace in NAMESPACES
        }
        exit_code = rescore(module, declared, canonical, lessons, report)
        require(file_digest(args.generator) == source_hash,
                "Generator source changed while the certificate was being scored",
                code="source_mismatch")
        report["integrity"] = {
            "runtime_manifest_hash_verified": True,
            "instance_hashes_verified": len(lessons),
            "accepted_pair_input_hashes_verified": report["summary"]["generated_pairs"],
            "canonical_ledger_hash_verified": True,
        }
        report["status"] = "ambiguous" if exit_code else "no_ambiguity_found"
    except CertificateError as error:
        report["errors"].append(error.detail)
        report["status"] = "error"
        exit_code = 2
    except Exception as error:
        report["errors"].append({"code": "malformed_or_scoring_error",
                                 "message": str(error), "error_type": type(error).__name__})
        report["status"] = "error"
        exit_code = 2
    report["execution"]["exit_code"] = exit_code
    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as handle:
            json.dump(report, handle, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
    except OSError as error:
        print(f"Could not write certificate: {error}", file=sys.stderr)
        return 2
    print(json.dumps({"status": report["status"], "exit_code": exit_code,
                      "output": str(args.output), "summary": report.get("summary"),
                      "errors": report["errors"]}, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
