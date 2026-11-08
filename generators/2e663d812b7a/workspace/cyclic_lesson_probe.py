#!/usr/bin/env python3
"""Rotate saved production lessons without generating or rerendering labels.

From the repository root::

    python generators/2e663d812b7a/workspace/cyclic_lesson_probe.py \
        --input var/lesson-census.json --out var/cyclic-lessons.json --canonical

The default generator is this task's selected ../generator.py. Competitors are
merged exactly as in the semantic gate: LESSON_COMPETITORS first, followed by
CANONICAL_SHORTCUTS using setdefault. Every materialized train+test pair becomes
the query once, with all other pairs in cyclic order as demonstrations. Counts
come from the census; this does not assume EXAMPLES_NEEDED or five-pair lessons.

Exit codes: 0 = no declared query ambiguity; 1 = a query-changing survivor;
2 = invalid/incomplete evidence, evaluation errors, or a hook disagreement.
An answer-equivalent ``survived_all`` rival alone does not cause failure.

The output includes the input-file SHA and a canonical-JSON payload SHA (with
that SHA field omitted). The small stdout receipt gives the complete output
file's SHA; a file cannot contain its own complete-file hash. --self-test uses
temporary fixtures only. No Racket runtime or reference execution is used.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import tempfile


sys.dont_write_bytecode = True
HERE = Path(__file__).resolve()
TASK_ID = "2e663d812b7a"
SUPPORT_DIR = next((directory for ancestor in HERE.parents
                    for directory in (ancestor, ancestor / "shared/runtime")
                    if (directory / "reviewer_support.py").is_file()), None)
if SUPPORT_DIR is None:
    raise FileNotFoundError(f"No local reviewer_support.py ancestor of {HERE}")
sys.path.insert(0, str(SUPPORT_DIR))
from reviewer_support import canonical_pairs, canonical_path, find_root, normalize_grid

ROOT = find_root(HERE)
GENERATOR_PATHS = (ROOT / "generators" / TASK_ID / "generator.py",
                   ROOT / "puzzle_generators/per_puzzle" / TASK_ID / "generator.py")
DEFAULT_GENERATOR = next((path for path in GENERATOR_PATHS if path.is_file()), GENERATOR_PATHS[0])


CENSUS_SCHEMA = "arcpuzzles-lesson-census-v1"
REPORT_SCHEMA = "2e663d812b7a-cyclic-lesson-probe-v1"
OUTCOMES = ("refuted", "survived_all", "query_discriminates", "error")
COMPLETE_STATUSES = {
    "no_declared_ambiguity", "ambiguous", "warning", "no_contract", "hook_only"
}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def short_error(exc):
    return f"{type(exc).__name__}: {exc}"[:300]


def add_error(report, message):
    report["error_count"] += 1
    if len(report["errors"]) < 20:
        report["errors"].append(message)


def load_generator(path, source):
    """Import the exact hashed source bytes, avoiding a stale bytecode cache."""
    name = "_cyclic_generator_" + sha256(source)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None:
        raise ImportError(f"Cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    sys.path.insert(0, str(path.parent))
    try:
        exec(compile(source, str(path), "exec"), module.__dict__)
    finally:
        sys.path.pop(0)
    return module


def declared_rivals(gen, report):
    rivals, memberships, collisions = {}, {}, []
    for attribute in ("LESSON_COMPETITORS", "CANONICAL_SHORTCUTS"):
        declaration = getattr(gen, attribute, {})
        if not isinstance(declaration, dict):
            add_error(report, f"{attribute}: expected a dict of named callables")
            continue
        for name, fn in declaration.items():
            if not isinstance(name, str) or not name or not callable(fn):
                add_error(report, f"{attribute}:{name!r}: expected a nonempty name and callable")
                continue
            memberships.setdefault(name, []).append(attribute)
            if name in rivals and rivals[name] is not fn:
                collisions.append(name)
            rivals.setdefault(name, fn)
    report["declarations"] = {
        "merge": "LESSON_COMPETITORS, then CANONICAL_SHORTCUTS via setdefault",
        "memberships": memberships,
        "shortcut_names_with_different_shadowed_callable": sorted(collisions),
        "unique_rivals": len(rivals),
    }
    if not rivals:
        add_error(report, "No callable LESSON_COMPETITORS or CANONICAL_SHORTCUTS were declared")
    return dict(sorted(rivals.items()))


def positive_int(value):
    return type(value) is int and value > 0


def validate_census(census, report):
    """Reject partial, malformed, or differently scoped production evidence."""
    if not isinstance(census, dict):
        add_error(report, "Census must be a JSON object")
        return None
    if census.get("schema") != CENSUS_SCHEMA:
        add_error(report, f"Expected schema {CENSUS_SCHEMA!r}, got {census.get('schema')!r}")
    if census.get("task_id") != TASK_ID:
        add_error(report, f"Census task_id must be {TASK_ID!r}")
    status = census.get("status")
    report["source_status"] = status
    if status not in COMPLETE_STATUSES:
        add_error(report, f"Census status {status!r} is not completed, error-free evidence")
        report["partial"] = status != "error"
    source_errors = census.get("errors", [])
    if not isinstance(source_errors, list):
        add_error(report, "Census errors must be a list")
    elif source_errors:
        add_error(report, f"Census records {len(source_errors)} source error(s): {str(source_errors[0])[:250]}")
        report["partial"] |= any("partial" in str(e).lower() for e in source_errors)
    execution = census.get("execution")
    if execution is not None:
        if not isinstance(execution, dict):
            add_error(report, "Census execution must be an object")
        else:
            expected_exit = 1 if status == "ambiguous" else 2 if status == "error" else 0
            if execution.get("timed_out") or execution.get("exit_code") != expected_exit:
                report["partial"] = True
                add_error(report, "Census execution timed out or its exit code disagrees with status")
    sampler = census.get("sampler")
    if not isinstance(sampler, dict):
        add_error(report, "Census sampler must be an object")
        return None
    required = ("per_band", "n_demos", "n_queries", "period")
    if any(not positive_int(sampler.get(k)) for k in required):
        add_error(report, "Sampler per_band, n_demos, n_queries, and period must be positive integers")
        return None
    bands = sampler.get("bands")
    if (not isinstance(bands, list) or not bands
            or any(b not in ("easy", "medium", "hard") for b in bands)
            or len(set(bands)) != len(bands)):
        add_error(report, "Sampler bands must be distinct easy/medium/hard values")
        return None
    if sampler.get("task_id") != TASK_ID:
        add_error(report, "Sampler task_id disagrees with this task")
    lessons = census.get("lessons")
    if not isinstance(lessons, list):
        add_error(report, "Census lessons must be a list")
        return None
    expected = len(bands) * sampler["per_band"]
    report["requested"] = {k: sampler[k] for k in (*required, "bands")}
    report["requested"]["lessons"] = expected
    report["requested"]["pairs_per_lesson"] = sampler["n_demos"] + sampler["n_queries"]
    if len(lessons) != expected:
        report["partial"] = True
        add_error(report, f"Census has {len(lessons)} lesson rows; sampler requires {expected}")
    return sampler


def validate_lesson(row, census, sampler, seen):
    if not isinstance(row, dict):
        raise ValueError("Lesson row must be an object")
    band, index = row.get("band"), row.get("index")
    if band not in sampler["bands"] or type(index) is not int or not 0 <= index < sampler["per_band"]:
        raise ValueError("Lesson band/index is outside the requested census")
    identity = (band, index)
    if identity in seen:
        raise ValueError(f"Duplicate lesson identity {identity}")
    seen.add(identity)
    expected_seed = int(sha256(f"lesson-census:v1:{TASK_ID}:{band}:{index}".encode())[:8], 16)
    if row.get("seed") != expected_seed or row.get("sample_index") != index:
        raise ValueError("Lesson replay seed/sample_index disagrees with census-v1 recipe")
    instance = row.get("instance")
    if not isinstance(instance, dict):
        raise ValueError("Lesson has no materialized instance")
    if row.get("instance_sha256") != digest(instance):
        raise ValueError("Materialized instance SHA-256 mismatch")
    for key, expected in (("task_id", TASK_ID), ("seed", expected_seed),
                          ("sample_index", index), ("rule_task_id", census.get("rule_task_id"))):
        if key in instance and instance[key] != expected:
            raise ValueError(f"Instance {key} disagrees with its census replay identity")
    pairs, identities = [], []
    for split, count_key in (("train", "n_demos"), ("test", "n_queries")):
        split_pairs = instance.get(split)
        if not isinstance(split_pairs, list) or len(split_pairs) != sampler[count_key]:
            raise ValueError(f"Instance {split} count disagrees with sampler {count_key}")
        for i, pair in enumerate(split_pairs):
            if not isinstance(pair, dict):
                raise ValueError(f"{split}[{i}] is not a pair object")
            normalized = deepcopy(pair)
            normalized["input"] = normalize_grid(pair.get("input"))
            normalized["output"] = normalize_grid(pair.get("output"))
            pairs.append(normalized)
            identities.append({"split": split, "split_pair_index": i})
    return pairs, identities


def empty_counts(names):
    return {
        "rotations": 0, "ambiguous_rotations": 0, "survived_all_rotations": 0,
        "rivals": {name: dict.fromkeys(OUTCOMES, 0) for name in names},
        "hook": dict.fromkeys(("checked", "claimed_ambiguity", "false_negative",
                               "false_positive", "errors", "unscorable"), 0),
    }


def first_difference(expected, actual):
    if len(expected) != len(actual) or len(expected[0]) != len(actual[0]):
        return {"expected_shape": [len(expected), len(expected[0])],
                "rival_shape": [len(actual), len(actual[0])]}
    for r, row in enumerate(expected):
        for c, value in enumerate(row):
            if value != actual[r][c]:
                return {"row": r, "column": c, "expected": value, "rival": actual[r][c]}
    return None


def add_example(report, category, example, maximum):
    bucket = report["examples"][category]
    if len(bucket) < maximum:
        bucket.append(example)


def score_lesson(row, pairs, identities, rivals, hook, report, maximum):
    predictions, failures = {}, {}
    for name, fn in rivals.items():
        predictions[name], failures[name] = [], []
        for pair_index, pair in enumerate(pairs):
            try:
                predictions[name].append(normalize_grid(fn(deepcopy(pair["input"]))))
            except Exception as exc:
                predictions[name].append(None)
                failures[name].append({"pair_index": pair_index, "error": short_error(exc)})
    matches = {name: [out == pair["output"] for out, pair in zip(outputs, pairs)]
               for name, outputs in predictions.items()}
    band = report["per_band"].setdefault(row["band"], {
        **empty_counts(rivals), "lessons": 0, "pairs": 0, "heldout_indices": {}
    })
    band["lessons"] += 1
    band["pairs"] += len(pairs)
    for heldout in range(len(pairs)):
        replay = {"task_id": TASK_ID, "band": row["band"], "lesson_index": row["index"],
                  "seed": row["seed"], "sample_index": row["sample_index"],
                  "heldout_index": heldout, **identities[heldout],
                  "instance_sha256": row["instance_sha256"]}
        slot = band["heldout_indices"].setdefault(str(heldout), empty_counts(rivals))
        aggregates = (report["totals"], band, slot)
        statuses = {}
        for name in rivals:
            disagreements = [i for i, match in enumerate(matches[name]) if not match]
            demo_disagreements = [i for i in disagreements if i != heldout]
            status = ("error" if failures[name] else "refuted" if demo_disagreements else
                      "query_discriminates" if disagreements else "survived_all")
            statuses[name] = status
            for aggregate in aggregates:
                aggregate["rivals"][name][status] += 1
            if status == "error":
                add_example(report, "rival_errors", {"replay": replay, "rival": name,
                            **failures[name][0]}, maximum)
            elif status in ("query_discriminates", "refuted"):
                diff_index = heldout if status == "query_discriminates" else demo_disagreements[0]
                example = {"replay": replay, "rival": name, "differing_pair_index": diff_index,
                           "first_difference": first_difference(pairs[diff_index]["output"],
                                                                predictions[name][diff_index])}
                add_example(report, status, example, maximum)
        changing = [name for name, status in statuses.items() if status == "query_discriminates"]
        for aggregate in aggregates:
            aggregate["rotations"] += 1
            aggregate["ambiguous_rotations"] += bool(changing)
            aggregate["survived_all_rotations"] += "survived_all" in statuses.values()
        if hook is not None:
            hook_counts = Counter(checked=1)
            try:
                # Cyclic ordering makes the original final test position retain
                # its original demonstration order for a one-query census.
                demos = pairs[heldout + 1:] + pairs[:heldout]
                reasons = hook(deepcopy(demos), deepcopy(pairs[heldout]))
                if not isinstance(reasons, (list, tuple)) or any(not isinstance(r, str) for r in reasons):
                    raise TypeError("lesson_identifiable must return list[str]")
                hook_counts["claimed_ambiguity"] = bool(reasons)
                if "error" in statuses.values():
                    hook_counts["unscorable"] = 1
                elif bool(reasons) != bool(changing):
                    mismatch = "false_positive" if reasons else "false_negative"
                    hook_counts[mismatch] = 1
                    add_example(report, "hook_mismatches", {"replay": replay, "kind": mismatch,
                                "query_changing_survivors": changing,
                                "reasons": [r[:300] for r in reasons[:maximum]]}, maximum)
            except Exception as exc:
                hook_counts["errors"] = 1
                add_example(report, "hook_errors", {"replay": replay, "error": short_error(exc)}, maximum)
            for aggregate in aggregates:
                for key, value in hook_counts.items():
                    aggregate["hook"][key] += value


def score_canonical(gen, rivals, report, maximum):
    """Optional comparison to saved canonical labels, never to a local renderer."""
    rule_task = getattr(gen, "RULE_TASK_ID", TASK_ID)
    path = canonical_path(ROOT)
    pairs = canonical_pairs(rule_task, root=ROOT)
    report["canonical"] = {"task_id": rule_task, "source_sha256": sha256(path.read_bytes()),
                           "pairs": len(pairs), "rivals": {}}
    for name, fn in rivals.items():
        counts, errors = Counter(), []
        for i, pair in enumerate(pairs):
            try:
                actual = normalize_grid(fn(deepcopy(pair["input"])))
                counts["fits" if actual == pair["output"] else "differs"] += 1
            except Exception as exc:
                counts["errors"] += 1
                if len(errors) < maximum:
                    errors.append({"pair_index": i, "variant": pair["variant"],
                                   "split": pair["split"], "error": short_error(exc)})
        report["canonical"]["rivals"][name] = {
            **{k: counts[k] for k in ("fits", "differs", "errors")}, "error_examples": errors
        }
        if counts["errors"]:
            add_error(report, f"Canonical evaluation: {name} raised on {counts['errors']} pair(s)")


def run_probe(input_path, generator_path=DEFAULT_GENERATOR, *, check_hook=True,
              check_canonical=False, maximum=4):
    input_path, generator_path = Path(input_path).resolve(), Path(generator_path).resolve()
    report = {
        "schema": REPORT_SCHEMA, "task_id": TASK_ID, "status": "error", "partial": False,
        "error_count": 0, "errors": [], "source": {"census_path": str(input_path),
            "generator_path": str(generator_path), "probe_sha256": sha256(HERE.read_bytes())},
        "rotation": "heldout=i; demos=(i+1..N-1,0..i-1) from stored train+test pairs",
        "limits": ["Finite declared-rival evidence, not a proof of identifiability.",
                   "Only stored materialized pairs are rotated; rejected draws are not reconstructed.",
                   "Hook comparison tests empty/nonempty reasons against the declared rival bank.",
                   "No generation, Racket execution, or reference rerendering is performed."],
        "examples": {key: [] for key in ("query_discriminates", "refuted", "rival_errors",
                                          "hook_mismatches", "hook_errors")},
        "per_band": {}, "pair_counts": {}, "demo_counts_per_rotation": {},
        "materialized_lessons_scored": 0, "unscored_lesson_rows": 0,
    }
    try:
        raw, source = input_path.read_bytes(), generator_path.read_bytes()
        census = json.loads(raw)
        report["source"].update(census_sha256=sha256(raw), generator_sha256=sha256(source))
        sampler = validate_census(census, report)
        if not isinstance(census, dict):
            return report
        recorded = census.get("generator_sha256")
        report["source"]["census_generator_sha256"] = recorded
        report["source"]["rule"] = {k: census.get(k) for k in (
            "rule_task_id", "rule_source_sha256", "rule_callable_sha256",
            "declared_rule_hash", "runtime_manifest_sha256", "controller_sha256")}
        if not isinstance(recorded, str) or not re.fullmatch(r"[0-9a-f]{64}", recorded):
            add_error(report, "Census generator_sha256 is missing or malformed")
            return report
        if recorded != sha256(source):
            add_error(report, "Census generator SHA-256 does not match current generator source")
            return report
        if sampler is None or census.get("schema") != CENSUS_SCHEMA or census.get("task_id") != TASK_ID:
            return report
        gen = load_generator(generator_path, source)
        for attribute in ("TASK_ID", "GENERATOR_ID"):
            if getattr(gen, attribute, None) != TASK_ID:
                add_error(report, f"Generator {attribute} does not identify this task")
        if census.get("rule_task_id") != getattr(gen, "RULE_TASK_ID", TASK_ID):
            add_error(report, "Census rule_task_id disagrees with generator rule task")
        report["generator_examples_needed"] = getattr(gen, "EXAMPLES_NEEDED", None)
        rivals = declared_rivals(gen, report)
        report["totals"] = empty_counts(rivals)
        hook = getattr(gen, "lesson_identifiable", None)
        report["hook"] = {"requested": check_hook, "available": callable(hook)}
        if check_hook and hook is not None and not callable(hook):
            add_error(report, "lesson_identifiable is declared but not callable")
        hook = hook if check_hook and callable(hook) else None
        if not rivals:
            return report
        seen, pair_counts, demo_counts = set(), Counter(), Counter()
        for row_index, row in enumerate(census["lessons"]):
            try:
                pairs, identities = validate_lesson(row, census, sampler, seen)
            except Exception as exc:
                report["unscored_lesson_rows"] += 1
                report["partial"] = True
                add_error(report, f"Lesson row {row_index}: {short_error(exc)}")
                continue
            row_errors = row.get("errors", [])
            if not isinstance(row_errors, list) or row_errors:
                add_error(report, f"Lesson {row['band']}:{row['index']} records census errors")
            score_lesson(row, pairs, identities, rivals, hook, report, maximum)
            report["materialized_lessons_scored"] += 1
            pair_counts[str(len(pairs))] += 1
            demo_counts[str(len(pairs) - 1)] += len(pairs)
        report["pair_counts"] = dict(sorted(pair_counts.items()))
        report["demo_counts_per_rotation"] = dict(sorted(demo_counts.items()))
        report["materialized_pairs_scored"] = sum(int(n) * count for n, count in pair_counts.items())
        if report["materialized_lessons_scored"] != report["requested"]["lessons"]:
            report["partial"] = True
            add_error(report, "Not all requested lesson rows were scored")
        if check_canonical:
            score_canonical(gen, rivals, report, maximum)
        totals = report["totals"]
        rival_errors = sum(counts["error"] for counts in totals["rivals"].values())
        if rival_errors:
            add_error(report, f"Rival evaluation failed in {rival_errors} rival/rotation comparisons")
        if totals["hook"]["errors"]:
            add_error(report, f"lesson_identifiable failed in {totals['hook']['errors']} rotations")
        mismatches = totals["hook"]["false_positive"] + totals["hook"]["false_negative"]
        if mismatches:
            add_error(report, f"lesson_identifiable disagrees with the declared rival bank in {mismatches} rotations")
        if generator_path.read_bytes() != source:
            add_error(report, "Generator source changed while the probe was running")
        if input_path.read_bytes() != raw:
            add_error(report, "Census file changed while the probe was running")
        report["status"] = ("error" if report["error_count"] else
                            "ambiguous" if totals["ambiguous_rotations"] else "no_declared_ambiguity")
    except Exception as exc:
        add_error(report, short_error(exc))
        report["status"] = "error"
    return report


def self_test():
    """Exercise rotation semantics and evidence failures with disposable inputs."""
    generator_text = '''TASK_ID = GENERATOR_ID = "2e663d812b7a"
EXAMPLES_NEEDED = 3
HOOK_MODE = "good"
def identity(g): return g
def only_one(g): return [[9]] if g == [[1]] else g
def only_five(g): return [[9]] if g == [[5]] else g
def always_wrong(g): return [[9]]
LESSON_COMPETITORS = {"identity": identity, "only_one": only_one,
                      "only_five": only_five, "always_wrong": always_wrong}
CANONICAL_SHORTCUTS = {"only_one": only_one, "shortcut_only": identity}
def lesson_identifiable(demos, query):
    if HOOK_MODE == "quiet": return []
    return [name for name, fn in LESSON_COMPETITORS.items()
            if all(fn(p["input"]) == p["output"] for p in demos)
            and fn(query["input"]) != query["output"]]
'''
    checks = []
    with tempfile.TemporaryDirectory(prefix="cyclic-lesson-probe-") as directory:
        root = Path(directory)
        generator_path, census_path = root / "generator.py", root / "census.json"
        generator_path.write_text(generator_text)
        seed = int(sha256(f"lesson-census:v1:{TASK_ID}:easy:0".encode())[:8], 16)
        pairs = [{"input": [[i]], "output": [[i]]} for i in range(1, 6)]
        instance = {"task_id": TASK_ID, "rule_task_id": TASK_ID, "seed": seed,
                    "sample_index": 0, "train": pairs[:4], "test": pairs[4:]}
        census = {"schema": CENSUS_SCHEMA, "task_id": TASK_ID, "rule_task_id": TASK_ID,
                  "generator_sha256": sha256(generator_path.read_bytes()), "status": "ambiguous",
                  "errors": [], "sampler": {"task_id": TASK_ID, "bands": ["easy"],
                  "per_band": 1, "n_demos": 4, "n_queries": 1, "period": 2},
                  "lessons": [{"band": "easy", "index": 0, "sample_index": 0, "seed": seed,
                               "instance": instance, "instance_sha256": digest(instance), "errors": []}]}

        def probe(value, **kwargs):
            census_path.write_text(json.dumps(value))
            return run_probe(census_path, generator_path, **kwargs)

        result = probe(census)
        assert result["status"] == "ambiguous" and result["error_count"] == 0, result
        assert result["totals"]["rotations"] == 5
        assert result["pair_counts"] == {"5": 1} and result["demo_counts_per_rotation"] == {"4": 5}
        assert result["declarations"]["unique_rivals"] == 5
        assert result["totals"]["rivals"]["identity"]["survived_all"] == 5
        assert result["totals"]["rivals"]["only_one"]["query_discriminates"] == 1
        assert result["totals"]["rivals"]["only_five"]["refuted"] == 4
        assert result["per_band"]["easy"]["heldout_indices"]["0"]["rivals"]["only_one"]["query_discriminates"] == 1
        assert result["totals"]["hook"]["checked"] == 5
        checks.extend(["all five query rotations", "answer-equivalent survival", "declaration merge", "hook agreement"])
        altered = deepcopy(census)
        altered["generator_sha256"] = "0" * 64
        assert probe(altered)["status"] == "error"
        checks.append("source mismatch rejected")
        altered = deepcopy(census)
        altered["status"] = "incomplete"
        result = probe(altered)
        assert result["status"] == "error" and result["partial"]
        checks.append("partial census rejected")
        altered = deepcopy(census)
        altered["lessons"][0]["instance_sha256"] = "0" * 64
        result = probe(altered)
        assert result["status"] == "error" and result["unscored_lesson_rows"] == 1
        checks.append("instance mutation rejected")
        altered = deepcopy(census)
        altered["sampler"]["n_demos"] = 3
        assert probe(altered)["status"] == "error"
        checks.append("split count mismatch rejected")
        generator_path.write_text(generator_text.replace('HOOK_MODE = "good"', 'HOOK_MODE = "quiet"'))
        census["generator_sha256"] = sha256(generator_path.read_bytes())
        result = probe(census)
        assert result["status"] == "error" and result["totals"]["hook"]["false_negative"] == 2
        assert probe(census, check_hook=False)["status"] == "ambiguous"
        checks.append("hook false negatives and opt-out")
    return {"schema": REPORT_SCHEMA, "status": "passed", "self_test_checks": checks}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("census", nargs="?", help="Production lesson-census JSON (or use --input)")
    parser.add_argument("--input", dest="input_path", help="Production lesson-census JSON")
    parser.add_argument("--out", help="Write the compact report JSON here")
    parser.add_argument("--generator", default=str(DEFAULT_GENERATOR), help="Selected generator.py path")
    parser.add_argument("--skip-hook", action="store_true", help="Do not call lesson_identifiable")
    parser.add_argument("--canonical", action="store_true", help="Also score saved canonical pairs")
    parser.add_argument("--max-examples", type=int, default=4, help="Maximum compact examples per category")
    parser.add_argument("--self-test", action="store_true", help="Run disposable semantic/evidence fixtures")
    args = parser.parse_args(argv)
    if args.max_examples < 0:
        parser.error("--max-examples must be nonnegative")
    if args.self_test:
        report = self_test()
    else:
        if bool(args.census) == bool(args.input_path) or not args.out:
            parser.error("Supply exactly one census path (positional or --input) and --out")
        input_path = args.input_path or args.census
        if Path(args.out).resolve() in {Path(input_path).resolve(), Path(args.generator).resolve(), HERE}:
            parser.error("--out must not overwrite the census, generator, or probe")
        report = run_probe(input_path, args.generator, check_hook=not args.skip_hook,
                           check_canonical=args.canonical, maximum=args.max_examples)
    report["report_payload_sha256"] = digest(report)
    if args.out:
        output_path = Path(args.out).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n")
        receipt = {"status": report["status"], "report_path": str(output_path),
                   "report_sha256": sha256(output_path.read_bytes()),
                   "report_payload_sha256": report["report_payload_sha256"],
                   "census_sha256": report.get("source", {}).get("census_sha256"),
                   "rotations": report.get("totals", {}).get("rotations", 0),
                   "ambiguous_rotations": report.get("totals", {}).get("ambiguous_rotations", 0),
                   "error_count": report.get("error_count", 0)}
        print(json.dumps(receipt, sort_keys=True))
    else:
        print(json.dumps(report, sort_keys=True))
    return 2 if report["status"] == "error" else 1 if report["status"] == "ambiguous" else 0


if __name__ == "__main__":
    raise SystemExit(main())
