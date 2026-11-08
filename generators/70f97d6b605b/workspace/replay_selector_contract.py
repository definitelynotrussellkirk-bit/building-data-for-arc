#!/usr/bin/env python3
"""Replay the selector contract with authentic labels from ``arcpuzzles apply``.

From the library root, with its documented runtime available::

    python generators/70f97d6b605b/workspace/replay_selector_contract.py \
        --out ../checks/selector-contract --seed 0 --samples-per-band 14

Every output directory must be new. Original apply receipts and subprocess
logs are retained alongside exact cases, replay arguments, and all failures.
Each band must include at least one agreed mixed draw for a passing replay.
Every firing witness must refute all of its linked semantic rivals; each lesson
competitor must have generated refutation evidence somewhere in the replay.
This is source-bound reviewer evidence, not an approval or training label.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback


TASK = "70f97d6b605b"
BANDS = ("easy", "medium", "hard")
NAMESPACES = ("SEMANTIC_RIVALS", "CANONICAL_SHORTCUTS", "LESSON_COMPETITORS")
MIXED_WITNESS = "complete_contrast_scene"
BATCH_SIZE = 64


def save_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def grid_hash(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def fail(failures, kind, **details):
    failures.append({"kind": kind, **details})


def callable_declaration(module, namespace, failures):
    declaration = getattr(module, namespace, None)
    result = {}
    if not isinstance(declaration, dict) or not declaration:
        fail(failures, "invalid_declaration", namespace=namespace,
             error="Expected a nonempty dict[str, callable(grid)].")
        return result
    for name, predictor in declaration.items():
        if not isinstance(name, str) or not name.strip() or not callable(predictor):
            fail(failures, "invalid_declaration", namespace=namespace,
                 member=repr(name), error="Names must be nonempty strings and values callable.")
        else:
            result[name] = predictor
    return result


def collect_declarations(module, failures):
    """Keep declaration namespaces separate; never silently omit a bad member."""
    return {namespace: callable_declaration(module, namespace, failures) for namespace in NAMESPACES}


def collect_witnesses(module, semantic_rivals, failures):
    witnesses = callable_declaration(module, "SEMANTIC_WITNESSES", failures)
    declared_links = getattr(module, "WITNESS_RIVALS", None)
    links = {}
    if not isinstance(declared_links, dict) or not declared_links:
        fail(failures, "invalid_declaration", namespace="WITNESS_RIVALS",
             error="Expected a nonempty witness-to-rival mapping")
        declared_links = {}
    for witness, names in declared_links.items():
        if witness not in witnesses:
            fail(failures, "invalid_declaration", namespace="WITNESS_RIVALS",
                 witness=repr(witness), error="Link names an undeclared witness")
            continue
        names = [names] if isinstance(names, str) else names
        if (not isinstance(names, (list, tuple)) or not names
                or any(not isinstance(name, str) or not name.strip() for name in names)):
            fail(failures, "invalid_declaration", namespace="WITNESS_RIVALS", witness=witness,
                 error="Expected a nonempty list of rival names or one rival string")
            continue
        links[witness] = list(names)
        if len(set(names)) != len(names):
            fail(failures, "invalid_declaration", namespace="WITNESS_RIVALS", witness=witness,
                 error="Duplicate linked rival names")
        for name in names:
            if name not in semantic_rivals:
                fail(failures, "invalid_declaration", namespace="WITNESS_RIVALS", witness=witness,
                     rival=name, error="Linked rival is absent from SEMANTIC_RIVALS")
    for witness in witnesses:
        if witness not in links:
            fail(failures, "invalid_declaration", namespace="WITNESS_RIVALS", witness=witness,
                 error="Declared witness has no valid rival links")
    if MIXED_WITNESS not in witnesses:
        fail(failures, "invalid_declaration", namespace="SEMANTIC_WITNESSES", witness=MIXED_WITNESS,
             error="The default mixed-scene witness is missing")
    return witnesses, links


def observe_witnesses(case, witnesses, failures):
    case["witnesses"] = {}
    for name, predicate in witnesses.items():
        try:
            fires = predicate(deepcopy(case["input"]))
            if type(fires) is not bool:
                raise TypeError("Witness predicates must return a boolean")
            case["witnesses"][name] = {"fires": fires}
        except Exception as exc:
            case["witnesses"][name] = {"error": f"{type(exc).__name__}: {exc}"}
            fail(failures, "witness_error", case=case["name"], witness=name,
                 error=case["witnesses"][name]["error"], traceback=traceback.format_exc())
    if case.get("default_mixed") is True and case["witnesses"].get(MIXED_WITNESS, {}).get("fires") is not True:
        fail(failures, "default_mixed_witness_not_fired", case=case["name"], witness=MIXED_WITNESS)


def check_witness_refutations(case, links, failures):
    """The local replay requires ALL linked rivals, not merely one counterexample."""
    scores = case.get("rivals", {}).get("SEMANTIC_RIVALS", {})
    for witness, names in links.items():
        if case.get("witnesses", {}).get(witness, {}).get("fires") is True:
            for name in names:
                score = scores.get(name, {})
                if score.get("matches_reference") is not False:
                    fail(failures, "witness_rival_not_refuted", case=case["name"], witness=witness,
                         rival=name, namespace="SEMANTIC_RIVALS", score=score, replay=case["replay"])


def bootstrap():
    """Import only helpers from the script's own library or copied runtime."""
    for ancestor in Path(__file__).resolve().parents:
        candidates = (ancestor / "shared/runtime", ancestor)
        helper = next((p for p in candidates if (p / "reviewer_support.py").is_file()), None)
        if helper is not None:
            sys.path.insert(0, str(helper))
            break
    else:
        raise FileNotFoundError("No task-local reviewer_support.py found")
    from reviewer_support import canonical_pairs, find_root, normalize_grid

    root = find_root(__file__)
    import_paths = [p for p in (root / "src", root / "shared/runtime", root) if p.is_dir()]
    sys.path[:0] = [str(p) for p in import_paths]
    return root, canonical_pairs, normalize_grid, import_paths


def apply_cases(root, out, cases, report, normalize_grid, import_paths):
    failures = report["failures"]
    usable = [case for case in cases if case.get("input") is not None]
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(str(p) for p in import_paths)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    report["apply_receipts"] = []
    first_rule = None
    for start in range(0, len(usable), BATCH_SIZE):
        batch = usable[start:start + BATCH_SIZE]
        stem = f"apply-{start // BATCH_SIZE:03d}"
        input_path, receipt_path = out / f"{stem}.inputs.json", out / f"{stem}.json"
        save_json(input_path, {"inputs": [case["input"] for case in batch]})
        argv = [sys.executable, "-m", "arcpuzzles", "--library", str(root),
                "apply", TASK, "--input", str(input_path), "--out", str(receipt_path),
                "--timeout", "180"]
        command = {"argv": argv, "cwd": str(root), "exit": None,
                   "case_names": [case["name"] for case in batch],
                   "environment": {key: env[key] for key in
                                   ("PYTHONPATH", "PYTHONDONTWRITEBYTECODE", "PYTHONNOUSERSITE",
                                    "TMPDIR", "RACKET_PATH") if key in env}}
        stdout = stderr = b""
        save_json(out / f"{stem}.command.json", command)
        try:
            completed = subprocess.run(argv, cwd=root, env=env, capture_output=True,
                                       timeout=195)
            command["exit"] = completed.returncode
            stdout, stderr = completed.stdout, completed.stderr
            if completed.returncode:
                fail(failures, "apply_runtime_error", batch=stem, exit=completed.returncode)
        except (OSError, subprocess.TimeoutExpired) as exc:
            command["error"] = f"{type(exc).__name__}: {exc}"
            stdout, stderr = getattr(exc, "stdout", b"") or b"", getattr(exc, "stderr", b"") or b""
            fail(failures, "apply_runtime_error", batch=stem, error=command["error"])
        finally:
            for suffix, content in (("stdout", stdout), ("stderr", stderr)):
                (out / f"{stem}.{suffix}").write_bytes(content)
            save_json(out / f"{stem}.command.json", command)
        if not receipt_path.is_file():
            fail(failures, "missing_apply_receipt", batch=stem)
            continue
        try:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            if not isinstance(receipt, dict):
                raise ValueError("Apply receipt must be an object")
        except (OSError, ValueError) as exc:
            fail(failures, "invalid_apply_receipt", batch=stem, error=str(exc))
            continue
        identity = {key: receipt.get(key) for key in
                    ("schema", "task_id", "rule_task_id", "reference", "rule_file",
                     "executed_rule_hash", "catalog_rule_hash", "rule_hash_matches_catalog",
                     "rule_text_sha256", "generator_sha256")}
        report["apply_receipts"].append({"path": receipt_path.name, "sha256": file_hash(receipt_path),
                                         "command": f"{stem}.command.json", **identity})
        expected_identity = {"schema": "arcpuzzles-apply-v1", "task_id": TASK, "rule_task_id": TASK,
                             "reference": "canonical", "rule_hash_matches_catalog": True,
                             "generator_sha256": report["generator_sha256"]}
        for key, expected in expected_identity.items():
            if identity[key] != expected:
                fail(failures, "invalid_apply_identity", batch=stem, field=key,
                     expected=expected, actual=identity[key])
        rule_identity = (identity["executed_rule_hash"], identity["rule_text_sha256"])
        if (not all(isinstance(value, str) and value for value in rule_identity)
                or identity["executed_rule_hash"] != identity["catalog_rule_hash"]):
            fail(failures, "invalid_apply_identity", batch=stem, error="Missing or inconsistent rule hashes")
        if first_rule is None:
            first_rule = rule_identity
        elif first_rule != rule_identity:
            fail(failures, "changed_rule_between_batches", batch=stem,
                 first=list(first_rule), actual=list(rule_identity))
        rows = receipt.get("results")
        if not isinstance(rows, list) or len(rows) != len(batch):
            fail(failures, "invalid_apply_results", batch=stem, expected_count=len(batch),
                 actual_count=len(rows) if isinstance(rows, list) else None)
        indexed = {}
        for row in rows if isinstance(rows, list) else []:
            index = row.get("index") if isinstance(row, dict) else None
            if type(index) is not int or not 0 <= index < len(batch) or index in indexed:
                fail(failures, "invalid_apply_result_index", batch=stem, row=row)
            else:
                indexed[index] = row
        for index, case in enumerate(batch):
            row = indexed.get(index)
            if row is None:
                fail(failures, "missing_apply_result", case=case["name"], batch=stem, index=index)
                continue
            if row.get("input") != case["input"] or row.get("error") is not None or row.get("valid_output") is not True:
                fail(failures, "invalid_apply_result", case=case["name"], batch=stem, row=row)
                continue
            try:
                output = normalize_grid(row.get("output"))
            except (TypeError, ValueError) as exc:
                fail(failures, "invalid_reference_output", case=case["name"], error=str(exc))
                continue
            case["reference"] = {"receipt": receipt_path.name, "index": index, "output": output,
                                 "input_sha256": row.get("input_sha256"),
                                 "output_sha256": row.get("output_sha256")}
            if "expected" in case and case["expected"] != output:
                fail(failures, "authoritative_output_mismatch", case=case["name"],
                     expected=case["expected"], actual=output)


def run_contract(args, out, report):
    root, canonical_pairs, normalize_grid, import_paths = bootstrap()
    task_dir = root / "generators" / TASK
    generator_path = task_dir / "generator.py"
    fixture_path = task_dir / "counterexamples/selector_cases.json"
    report.update(library=str(root), generator=str(generator_path.relative_to(root)),
                  generator_sha256=file_hash(generator_path), fixture_sha256=file_hash(fixture_path),
                  verifier_sha256=file_hash(Path(__file__)))
    spec = importlib.util.spec_from_file_location(f"selector_contract_generator_{TASK}", generator_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load selected generator: {generator_path}")
    generator = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = generator
    spec.loader.exec_module(generator)
    report["lesson_schedule_period"] = getattr(generator, "LESSON_SCHEDULE_PERIOD", None)
    failures = report["failures"]
    rivals = collect_declarations(generator, failures)
    witnesses, witness_links = collect_witnesses(generator, rivals["SEMANTIC_RIVALS"], failures)
    report["declarations"] = {namespace: sorted(members) for namespace, members in rivals.items()}
    report["witness_declarations"] = {"predicates": sorted(witnesses), "links": witness_links}
    cases = report["cases"] = []
    for pair in canonical_pairs(TASK, root=root, labeled_only=True):
        replay = {key: pair[key] for key in ("variant", "split", "pair_index")}
        cases.append({"name": f"canonical:v{pair['variant']}:{pair['split']}:{pair['pair_index']}",
                      "source": "canonical", "replay": replay,
                      "input": pair["input"], "expected": pair["output"]})
    if not cases:
        fail(failures, "missing_canonical_pairs", error="No usable labeled canonical pairs")
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    if (not isinstance(fixture, dict) or fixture.get("task_id") != TASK
            or not isinstance(fixture.get("cases"), list) or not fixture["cases"]):
        raise ValueError("Invalid or empty selector_cases.json")
    fixture_names = set()
    for index, item in enumerate(fixture["cases"]):
        name = item.get("name") if isinstance(item, dict) else None
        if not isinstance(name, str) or not name or name in fixture_names:
            raise ValueError(f"Invalid or duplicate fixture name at index {index}")
        fixture_names.add(name)
        cases.append({"name": f"fixture:{name}", "source": "fixture",
                      "replay": {"path": str(fixture_path.relative_to(root)), "index": index, "name": name},
                      "input": normalize_grid(item.get("input")),
                      "expected": normalize_grid(item.get("expected"))})
    for band in BANDS:
        for index in range(args.samples_per_band):
            case = {"name": f"generated:{band}:seed{args.seed}:sample{index}", "source": "generated",
                    "replay": {"seed": args.seed, "sample_index": index, "difficulty": band, "overrides": {}},
                    "input": None}
            cases.append(case)
            generated = False
            raw_input = None
            try:
                raw_input = generator.generate(args.seed, index, difficulty=band)
                generated = True
                case["input"] = normalize_grid(raw_input)
            except Exception as exc:
                if generated:
                    case["rejected_input"] = {"type": type(raw_input).__name__, "repr": repr(raw_input)}
                    try:
                        json.dumps(raw_input)
                        case["rejected_input"]["value"] = raw_input
                    except (TypeError, ValueError):
                        pass
                fail(failures, "generation_error", case=case["name"], replay=case["replay"],
                     error=f"{type(exc).__name__}: {exc}", traceback=traceback.format_exc())
                continue
            try:
                scheduled = generator.schedule_profile(args.seed, index, difficulty=band)
                observed = generator.observe_overrides(deepcopy(case["input"]))
                case["scheduled_profile"] = scheduled
                case["observed_overrides"] = observed
                if scheduled not in ("core", "mixed") or not isinstance(observed, dict):
                    raise ValueError("Expected a core/mixed schedule and an observed override dictionary")
                if observed.get("scene") != scheduled:
                    raise ValueError(f"Scheduled scene {scheduled!r} differs from observed scene {observed.get('scene')!r}")
                case["default_mixed"] = scheduled == "mixed"
            except Exception as exc:
                fail(failures, "invalid_schedule_observation", case=case["name"], replay=case["replay"],
                     error=f"{type(exc).__name__}: {exc}", traceback=traceback.format_exc())
    for band in BANDS:
        if not any(case["replay"].get("difficulty") == band and case.get("default_mixed") is True for case in cases):
            fail(failures, "missing_mixed_coverage", difficulty=band,
                 error="No agreed default mixed draw was generated in this band")
    for case in cases:
        if case["input"] is None:
            continue
        case["input_sha256"] = grid_hash(case["input"])
        try:
            errors = generator.self_check(deepcopy(case["input"]), difficulty=case["replay"].get("difficulty"))
            if not isinstance(errors, (list, tuple)) or any(not isinstance(error, str) for error in errors):
                raise TypeError("self_check must return a list or tuple of error strings")
            case["self_check_errors"] = list(errors)
            for error in errors:
                fail(failures, "self_check_rejection", case=case["name"], replay=case["replay"], error=error)
        except Exception as exc:
            case["self_check_errors"] = [f"{type(exc).__name__}: {exc}"]
            fail(failures, "self_check_error", case=case["name"], error=case["self_check_errors"][0],
                 traceback=traceback.format_exc())
        observe_witnesses(case, witnesses, failures)
    save_json(out / "cases.json", {"task_id": TASK, "generator_sha256": report["generator_sha256"], "cases": cases})
    apply_cases(root, out, cases, report, normalize_grid, import_paths)
    for case in cases:
        if "reference" not in case:
            continue
        output = case["reference"]["output"]
        case["rivals"] = {}
        for namespace, members in rivals.items():
            scores = case["rivals"][namespace] = {}
            for name, predictor in members.items():
                try:
                    prediction = normalize_grid(predictor(deepcopy(case["input"])))
                    matches = prediction == output
                    scores[name] = {"matches_reference": matches, "prediction_sha256": grid_hash(prediction)}
                    if namespace == "CANONICAL_SHORTCUTS" and case["source"] == "canonical" and not matches:
                        fail(failures, "canonical_shortcut_failed_to_fit", case=case["name"], rival=name,
                             prediction=prediction, reference=output)
                except Exception as exc:
                    scores[name] = {"error": f"{type(exc).__name__}: {exc}"}
                    fail(failures, "rival_error", case=case["name"], namespace=namespace, rival=name,
                         error=scores[name]["error"], traceback=traceback.format_exc())
        check_witness_refutations(case, witness_links, failures)
    groups = {source: [case for case in cases if case["source"] == source]
              for source in ("canonical", "fixture", "generated")}
    groups["generated_mixed"] = [case for case in cases if case.get("default_mixed") is True]
    groups["generated_core"] = [case for case in cases if case.get("default_mixed") is False]
    for band in BANDS:
        groups[band] = [case for case in cases if case["replay"].get("difficulty") == band]
        groups[f"{band}_mixed"] = [case for case in groups[band] if case.get("default_mixed") is True]
        groups[f"{band}_core"] = [case for case in groups[band] if case.get("default_mixed") is False]
    report["rival_counts"] = {}
    for namespace, members in rivals.items():
        report["rival_counts"][namespace] = {}
        for name in members:
            counts = report["rival_counts"][namespace][name] = {}
            for group, selected in groups.items():
                scores = [c.get("rivals", {}).get(namespace, {}).get(name, {}) for c in selected]
                counts[group] = {"total": len(selected),
                                 "evaluated": sum("matches_reference" in score for score in scores),
                                 "fit": sum(score.get("matches_reference") is True for score in scores),
                                 "refuted": sum(score.get("matches_reference") is False for score in scores),
                                 "errors": sum("error" in score for score in scores)}
    for name, counts in report["rival_counts"]["LESSON_COMPETITORS"].items():
        if counts["generated"]["refuted"] == 0:
            fail(failures, "lesson_competitor_has_no_generated_refutation", rival=name,
                 per_band={band: counts[band] for band in BANDS})
    report["witness_counts"] = {}
    for witness in witnesses:
        linked = witness_links.get(witness, [])
        counts = report["witness_counts"][witness] = {"linked_rivals": linked, "groups": {}}
        for group, selected in groups.items():
            firing = [case for case in selected if case.get("witnesses", {}).get(witness, {}).get("fires") is True]
            counts["groups"][group] = {
                "total": len(selected), "fires": len(firing),
                "evaluated": sum("fires" in case.get("witnesses", {}).get(witness, {}) for case in selected),
                "errors": sum("error" in case.get("witnesses", {}).get(witness, {}) for case in selected),
                "all_linked_refuted": sum(bool(linked) and all(
                    case.get("rivals", {}).get("SEMANTIC_RIVALS", {}).get(name, {}).get("matches_reference") is False
                    for name in linked) for case in firing),
                "linked_refutations": {name: sum(
                    case.get("rivals", {}).get("SEMANTIC_RIVALS", {}).get(name, {}).get("matches_reference") is False
                    for case in firing) for name in linked},
            }
        if counts["groups"]["generated"]["fires"] == 0:
            fail(failures, "missing_generated_witness_coverage", witness=witness,
                 per_band={band: counts["groups"][band] for band in BANDS})
    report["case_counts"] = {source: sum(case["source"] == source for case in cases)
                             for source in ("canonical", "fixture", "generated")}
    report["case_counts"]["generated_mixed"] = sum(case.get("default_mixed") is True for case in cases)
    report["case_counts"]["generated_core"] = sum(case.get("default_mixed") is False for case in cases)
    report["generator_sha256_after"] = file_hash(generator_path)
    if report["generator_sha256_after"] != report["generator_sha256"]:
        fail(failures, "generator_changed_during_replay", before=report["generator_sha256"],
             after=report["generator_sha256_after"])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, required=True, help="new evidence directory")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--samples-per-band", type=int, default=14)
    args = parser.parse_args(argv)
    if args.samples_per_band < 1:
        parser.error("--samples-per-band must be positive")
    out = args.out.resolve()
    try:
        out.mkdir(parents=True, exist_ok=False)
    except OSError as exc:
        print(f"Cannot create new output directory {out}: {exc}", file=sys.stderr)
        return 2
    report = {"schema": "arcpuzzles-selector-contract-v1", "task_id": TASK,
              "seed": args.seed, "samples_per_band": args.samples_per_band,
              "command": {"argv": [sys.executable, str(Path(__file__).resolve()),
                                   *(sys.argv[1:] if argv is None else argv)], "cwd": str(Path.cwd())},
              "policy": "Canonical labels and fixtures must agree with apply; scheduled and observed scenes must agree; complete_contrast_scene must fire on every default mixed draw; every firing witness must refute ALL linked SEMANTIC_RIVALS; each LESSON_COMPETITOR needs a generated refutation; each witness needs generated coverage. Band counts and mixed coverage are retained separately.",
              "failures": []}
    try:
        run_contract(args, out, report)
    except Exception as exc:
        fail(report["failures"], "runtime_error", error=f"{type(exc).__name__}: {exc}", traceback=traceback.format_exc())
    report["status"] = "failed" if report["failures"] else "passed"
    report["exit"] = 1 if report["failures"] else 0
    save_json(out / "failures.json", report["failures"])
    save_json(out / "report.json", report)
    print(json.dumps({"status": report["status"], "out": str(out), "failures": len(report["failures"]),
                      "case_counts": report.get("case_counts", {}), "generator_sha256": report.get("generator_sha256")}, sort_keys=True))
    return report["exit"]


if __name__ == "__main__":
    raise SystemExit(main())
