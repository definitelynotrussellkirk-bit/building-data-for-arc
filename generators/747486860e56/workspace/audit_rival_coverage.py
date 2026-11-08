#!/usr/bin/env python3
"""Audit existing shared lesson receipts; never sample or execute a reference.

Usage:
  python audit_rival_coverage.py census.json[.gz] --out summary.json
  python audit_rival_coverage.py rescore.json --canonical-census current.json --out summary.json

Exit0: no finite gap found; exit1: finite coverage gap; exit2: invalid/missing
evidence. A gap means a rival fails canonical labels yet survives every sampled
generated label. Counts describe scored lessons/holdouts, not mismatching pairs.
Namespaces stay separate: the receipt has no callable declaration identities.
"""
from collections import Counter
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys
import zlib


COMPLETE = {"no_ambiguity_found", "no_declared_ambiguity", "warning", "ambiguous"}
SCORES = {"refuted", "survived_all", "ambiguous"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def source_hash(value, field):
    require(isinstance(value, str) and len(value) == 64
            and all(c in "0123456789abcdef" for c in value), f"invalid {field}")
    return value


def integer(value, field, minimum=0):
    require(type(value) is int and value >= minimum, f"invalid {field}")
    return value


def valid_grid(grid):
    return (isinstance(grid, list) and bool(grid) and isinstance(grid[0], list) and bool(grid[0])
            and all(isinstance(row, list) and len(row) == len(grid[0])
                    and all(type(v) is int and 0 <= v <= 9 for v in row) for row in grid))


def validate(report):
    require(isinstance(report, dict), "expected a receipt object")
    schema = report.get("schema")
    require(schema in {"arcpuzzles-lesson-census-v1", "arcpuzzles-lesson-rescore-v1"}, "unsupported receipt schema")
    require(isinstance(report.get("task_id"), str) and report["task_id"].isalnum(), "invalid task_id")
    for field in ("status", "production_status"):
        require(report.get(field) in COMPLETE, f"{field} incomplete, errored or has no rival contract")
    require(report.get("rotation_status") in COMPLETE | {"not_requested"}, "rotation_status incomplete or errored")
    require(report.get("errors") == [], "receipt contains errors")
    execution = report.get("execution", {})
    require(isinstance(execution, dict), "malformed execution evidence")
    require(execution.get("timed_out") is False and type(execution.get("exit_code")) is int
            and execution["exit_code"] == (1 if report["status"] == "ambiguous" else 0), "receipt execution incomplete")
    census = schema == "arcpuzzles-lesson-census-v1"
    if census:
        names = report.get("rivals")
        require(isinstance(names, list), "missing declared rivals")
        for field in ("generator_sha256", "rule_source_sha256", "rule_callable_sha256"):
            source_hash(report.get(field), field)
    else:
        require(isinstance(report.get("rival_summary"), dict), "missing rescore rival declarations")
        names = list(report["rival_summary"])
        require(report.get("rival_source_stable") is True, "rescore rival source was not stable")
        for field in ("input_generator_sha256", "rival_generator_sha256", "retained_rule_source_sha256", "retained_rule_callable_sha256"):
            source_hash(report.get(field), field)
    require(bool(names) and all(isinstance(n, str) and n for n in names)
            and len(names) == len(set(names)), "invalid or empty rival declarations")
    names = sorted(names)
    lessons, summary = report.get("lessons"), report.get("summary", {})
    require(isinstance(summary, dict), "malformed summary")
    require(isinstance(lessons, list) and bool(lessons), "missing generated lessons")
    if census:
        require(integer(summary.get("requested"), "requested", 1)
                == integer(summary.get("materialized"), "materialized", 1) == len(lessons), "partial lesson census")
        for field in ("materialization_errors", "scoring_errors", "rotation_scoring_errors"):
            require(summary.get(field) == 0 and type(summary[field]) is int, f"receipt reports {field}")
    else:
        require(integer(summary.get("lessons"), "lessons", 1) == len(lessons), "partial rescore")
    totals = {name: {"production": Counter(), "rotations": Counter()} for name in names}
    rotations_total = pairs_total = 0
    identities, bands = set(), Counter()
    for i, lesson in enumerate(lessons):
        require(isinstance(lesson, dict), "malformed lesson")
        identity = (lesson.get("band"), lesson.get("index"))
        require(isinstance(identity[0], str) and type(identity[1]) is int
                and identity not in identities, "invalid/duplicate lesson identity")
        identities.add(identity)
        bands[identity[0]] += 1
        instance = lesson.get("instance", {})
        require(isinstance(instance, dict) and digest(instance) == lesson.get("instance_sha256"), "instance hash mismatch")
        train, tests = instance.get("train"), instance.get("test")
        tests = [tests] if isinstance(tests, dict) else tests
        require(isinstance(train, list) and bool(train) and isinstance(tests, list) and bool(tests), "missing labelled pairs")
        pairs = train + tests
        require(all(isinstance(p, dict) and valid_grid(p.get("input")) and valid_grid(p.get("output")) for p in pairs), "malformed labelled grids")
        pairs_total += len(pairs)
        rotations = lesson.get("rotations")
        require(isinstance(rotations, list) and all(isinstance(r, dict) for r in rotations), "missing/malformed rotation evidence")
        rotated = report["rotation_status"] != "not_requested"
        if rotated:
            require(len(tests) == 1 and len(rotations) == len(pairs), "incomplete pair holdouts")
            require([r.get("query_index") for r in rotations] == list(range(len(pairs)))
                    and all(r.get("train_indices") == [j for j in range(len(pairs)) if j != r["query_index"]]
                            for r in rotations), "invalid rotation indices")
        else:
            require(not rotations, "unexpected rotations")
        rotations_total += len(rotations)
        if rotated:
            require(all((lesson.get("rivals", {}).get(name) == "survived_all")
                        == all(r.get("rivals", {}).get(name) == "survived_all" for r in rotations)
                        for name in names), "lesson survival contradicts complete holdouts")
        for scope, rows in (("production", [lesson]), ("rotations", rotations)):
            for row in rows:
                require(row.get("errors") == [], "lesson/rotation contains scoring errors")
                scores = row.get("rivals")
                require(isinstance(scores, dict) and set(scores) == set(names), "missing/extra scored rival")
                require(all(v in SCORES for v in scores.values()), "rival score missing or errored")
                require(type(row.get("ambiguous")) is bool
                        and row["ambiguous"] == ("ambiguous" in scores.values()), "inconsistent ambiguity evidence")
                for name, score in scores.items():
                    totals[name][scope][score] += 1
    require(integer(summary.get("rotations"), "rotations") == rotations_total, "rotation total mismatch")
    production_ambiguous = any(l["ambiguous"] for l in lessons)
    rotations_ambiguous = any(r["ambiguous"] for l in lessons for r in l["rotations"])
    require((report["production_status"] == "ambiguous") == production_ambiguous, "production verdict contradicts scores")
    require((report["rotation_status"] == "ambiguous") == rotations_ambiguous, "rotation verdict contradicts scores")
    if census:
        require(integer(summary.get("pairs"), "pairs", 1) == pairs_total, "pair total mismatch")
        sampler = report.get("sampler", {})
        require(isinstance(sampler, dict) and isinstance(report.get("per_band"), dict), "malformed sampler/band evidence")
        demos = integer(sampler.get("n_demos"), "n_demos", 1)
        queries = integer(sampler.get("n_queries"), "n_queries", 1)
        requested = integer(sampler.get("per_band"), "per_band", 1)
        require(isinstance(sampler.get("bands"), list) and len(sampler["bands"]) == len(set(sampler["bands"]))
                and set(sampler["bands"]) == set(bands), "incomplete sampler band coverage")
        require(set(report.get("per_band", {})) == set(bands), "band summary mismatch")
        for band, count in bands.items():
            row = report["per_band"][band]
            require(isinstance(row, dict), "malformed band summary")
            require(row.get("requested") == row.get("materialized") == count == requested, "partial band census")
            require({index for name, index in identities if name == band} == set(range(requested)), "missing band indices")
        require(all(len(l["instance"]["train"]) == demos
                    and len(l["instance"]["test"] if isinstance(l["instance"]["test"], list) else [l["instance"]["test"]]) == queries
                    for l in lessons), "incomplete requested pairs")
        require(type(sampler.get("rotate_query")) is bool
                and sampler["rotate_query"] == (report["rotation_status"] != "not_requested"), "rotation setting mismatch")
        if sampler.get("enumerate_schedule_period", False):
            coverage = report.get("schedule_coverage", {})
            require(isinstance(coverage, dict) and coverage.get("status") == "complete_fixed_seed"
                    and coverage.get("expected_lessons") == len(lessons)
                    and coverage.get("expected_rotations") == rotations_total, "incomplete schedule enumeration")
    return names, totals, pairs_total, rotations_total


def analyze(report, canonical_census=None):
    names, totals, pairs_total, rotations_total = validate(report)
    is_rescore = report["schema"] == "arcpuzzles-lesson-rescore-v1"
    require(is_rescore or canonical_census is None, "direct census uses its own canonical evidence; omit --canonical-census")
    canonical = canonical_census if is_rescore else report
    if is_rescore:
        require(canonical_census is not None, "rescore has no canonical fit: supply --canonical-census")
        canonical_names, _, _, _ = validate(canonical)
        require(canonical["schema"] == "arcpuzzles-lesson-census-v1", "canonical evidence must be a census")
        for current, retained in (("generator_sha256", "rival_generator_sha256"),
                                  ("rule_source_sha256", "retained_rule_source_sha256"),
                                  ("rule_callable_sha256", "retained_rule_callable_sha256"), ("task_id", "task_id")):
            require(canonical[current] == report[retained], f"canonical join mismatch: {current}")
        require(set(canonical_names) == set(names), "canonical join rival declarations differ")
    count = integer(canonical.get("canonical_pairs"), "canonical_pairs", 1)
    fits = canonical.get("canonical_rival_fit")
    require(isinstance(fits, dict) and set(fits) == set(names), "missing canonical rival fit evidence")
    rows, gaps = {}, []
    for name in names:
        row = fits[name]
        require(isinstance(row, dict) and row.get("errors") == [], f"canonical scoring incomplete/error: {name}")
        require(integer(row.get("pairs"), "canonical rival pairs", 1) == count, "canonical pair count mismatch")
        matched = integer(row.get("fits"), "canonical fits")
        require(matched <= count and row.get("status") == ("fits_all" if matched == count else "refuted"), "inconsistent canonical fit")
        production, rotations = totals[name]["production"], totals[name]["rotations"]
        all_generated_fit = production["survived_all"] == len(report["lessons"])
        require(not all_generated_fit or rotations["survived_all"] == rotations_total, "survival/rotation disagreement")
        gap = matched < count and all_generated_fit
        if gap:
            gaps.append(name)
        rows[name] = {"canonical_pairs": count, "canonical_fits": matched,
                      "canonical_refutations": count-matched,
                      "generated_refuted_lessons": production["refuted"],
                      "generated_ambiguous_lessons": production["ambiguous"],
                      "generated_survived_all_lessons": production["survived_all"],
                      "production_counts": dict(production), "rotation_counts": dict(rotations),
                      "survives_every_sampled_generated_label": all_generated_fit,
                      "finite_coverage_gap": gap}
    return {"schema": "task-rival-coverage-v1", "task_id": report["task_id"],
            "status": "finite_coverage_gap" if gaps else "no_finite_coverage_gap_found",
            "input_schema": report["schema"], "input_status": report["status"],
            "input_generator_sha256": report.get("input_generator_sha256", report.get("generator_sha256")),
            "rival_generator_sha256": report.get("rival_generator_sha256", report.get("generator_sha256")),
            "rule_source_sha256": canonical["rule_source_sha256"],
            "rule_callable_sha256": canonical["rule_callable_sha256"],
            "generated_lessons": len(report["lessons"]), "generated_pair_occurrences": pairs_total,
            "rotations": rotations_total, "coverage_gaps": gaps, "rivals": rows,
            "limits": ["Finite sampled coverage, not a proof about all inputs or universal identifiability.",
                       "Lesson refutation counts are not counts of mismatching pairs; rotations reuse the same labels.",
                       "Names remain separate because receipt data does not establish callable declaration identity.",
                       "Receipt labels and scoring are consumed without new sampling, rival execution or Racket execution."]}


def read_receipt(path):
    data = Path(path).read_bytes()
    decoded = gzip.decompress(data) if data.startswith(b"\x1f\x8b") else data
    return json.loads(decoded), hashlib.sha256(data).hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt")
    parser.add_argument("--canonical-census")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    try:
        receipt, input_hash = read_receipt(args.receipt)
        canonical, canonical_hash = read_receipt(args.canonical_census) if args.canonical_census else (None, None)
        summary = analyze(receipt, canonical)
        summary.update(input_sha256=input_hash, canonical_census_sha256=canonical_hash,
                       tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
        code = 1 if summary["coverage_gaps"] else 0
    except (ValueError, KeyError, TypeError, OSError, EOFError, zlib.error) as exc:
        summary = {"schema": "task-rival-coverage-v1", "status": "error", "errors": [f"{type(exc).__name__}: {exc}"]}
        code = 2
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2) + "\n")
    print(f"{summary['status']}: {len(summary.get('coverage_gaps', []))} gap(s); {output}")
    return code


if __name__ == "__main__":
    sys.exit(main())
