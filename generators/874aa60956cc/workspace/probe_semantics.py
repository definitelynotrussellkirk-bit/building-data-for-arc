#!/usr/bin/env python3
"""Finite, provisional Python semantic evidence for task 874aa60956cc.

Run from any directory, in the library or a copied runtime::

    python3 path/to/probe_semantics.py --out var/874aa60956cc-python-probe.json

The defaults draw indices 0..99 at seed 17 in easy, medium, and hard. This
authoring probe reads canonical answers and must not be used during a blind
solve. It discovers the generator's actual shortcut/competitor declarations.
Generated outputs are the generator's Python authoring mirror, NOT reference
labels. Confirm retained inputs with public Catalog.apply / arcpuzzles apply
before treating them as Racket-verified counterexamples. No finite rival set
establishes universal lesson identifiability.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


TASK_ID = "874aa60956cc"
RIVAL_NAMESPACES = ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS")


def _bootstrap_support():
    here = Path(__file__).resolve()
    for ancestor in here.parents:
        for relative in ("reviewer_support.py", "shared/runtime/reviewer_support.py"):
            support = ancestor / relative
            if support.is_file():
                sys.path.insert(0, str(support.parent))
                return support
    raise RuntimeError("Cannot find reviewer_support.py in this probe's own library/runtime tree")


_SUPPORT_PATH = _bootstrap_support()
from reviewer_support import canonical_pairs, canonical_path, find_root, normalize_grid  # noqa: E402


def _digest(value):
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _file_digest(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _generator_path(root):
    candidates = (
        root / "generators" / TASK_ID / "generator.py",
        root / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py",
    )
    for path in candidates:
        if path.is_file():
            return path
    raise FileNotFoundError("Selected task generator not found: " + ", ".join(map(str, candidates)))


def _load_generator(path):
    name = f"probe_generator_{TASK_ID}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _contracts(module):
    missing = []
    if not callable(getattr(module, "_predict", None)):
        missing.append("callable _predict(grid, policy='intended') authoring mirror")
    rivals = {}
    for namespace in RIVAL_NAMESPACES:
        declaration = getattr(module, namespace, None)
        if not isinstance(declaration, dict) or not declaration:
            missing.append(f"nonempty {namespace} dictionary")
            continue
        for name, solve in declaration.items():
            if not isinstance(name, str) or not name or not callable(solve):
                missing.append(f"{namespace} contains a non-string name or non-callable rival")
            else:
                rivals[f"{namespace}:{name}"] = (namespace, name, solve)
    witnesses = getattr(module, "SEMANTIC_WITNESSES", None)
    if not isinstance(witnesses, dict) or not witnesses:
        missing.append("nonempty SEMANTIC_WITNESSES dictionary")
        witnesses = {}
    elif any(not isinstance(name, str) or not name or not callable(fn)
             for name, fn in witnesses.items()):
        missing.append("SEMANTIC_WITNESSES contains an invalid name or predicate")
    return rivals, witnesses, missing


def _predict(solve, grid, **kwargs):
    return normalize_grid(solve(deepcopy(grid), **kwargs))


def _case(grid, prediction, *, seed, sample_index, difficulty):
    return {
        "seed": seed, "sample_index": sample_index, "difficulty": difficulty,
        "input_sha256": _digest(grid), "input": deepcopy(grid),
        "provisional_python_output": deepcopy(prediction),
        "provisional_python_output_sha256": _digest(prediction),
        "reference_validation": "pending_public_racket_apply",
    }


def _canonical_identity(pair):
    return {name: pair[name] for name in ("variant", "split", "pair_index")}


def _run(args):
    root = find_root(__file__)
    generator_path = _generator_path(root)
    ledger = canonical_path(root)
    tracked = [Path(__file__).resolve(), generator_path, _SUPPORT_PATH, ledger]
    for relative in ("puzzle_generators/base.py", "puzzle_generators/helpers/grid.py"):
        candidate = _SUPPORT_PATH.parent / relative
        if candidate.is_file():
            tracked.append(candidate)
    source_hashes = {str(path): _file_digest(path) for path in tracked}
    selected_records = []
    with ledger.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    selected_records.append(row)
    report = {
        "schema": "874aa60956cc-python-semantic-probe-v1",
        "task_id": TASK_ID,
        "status": "running",
        "evidence_basis": "finite_python_authoring_mirror_comparison",
        "reference_labels_confirmed_for_generated_inputs": False,
        "limits": [
            "Generated expected outputs are provisional Python predictions; confirm them with public Racket apply.",
            "Canonical rival fit uses all labeled canonical variants, including available test labels.",
            "Witness rates and rival refutations concern only the listed draws and declared alternatives.",
            "This probe does not materialize lessons, certify identifiability, grant approval, or admit training data.",
        ],
        "settings": {"seed": args.seed, "samples_per_band": args.samples,
                     "start_index": args.start, "bands": args.bands},
        "source": {
            "root": str(root), "generator": str(generator_path),
            "files_sha256": source_hashes,
            "selected_canonical_records_sha256": _digest(selected_records),
            "canonical_rule_text_sha256": [
                hashlib.sha256(row.get("program_solution", "").encode("utf-8")).hexdigest()
                for row in selected_records
            ],
        },
        "errors": [], "coverage_gaps": [],
    }
    module = _load_generator(generator_path)
    rivals, witnesses, missing = _contracts(module)
    if missing:
        report["status"] = "blocked_missing_contract"
        report["errors"] = missing
        report["remedy"] = "Run after the selected generator declares the authoring mirror, rivals, and witnesses."
        return report, 2

    pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    if not pairs:
        raise ValueError("No labeled canonical pairs; canonical fit cannot be checked")
    report["canonical_pairs"] = [
        {**_canonical_identity(pair), "input_sha256": _digest(pair["input"]),
         "output_sha256": _digest(pair["output"])} for pair in pairs
    ]
    report["canonical_mirror_matches"] = 0
    report["rivals"] = {
        key: {"namespace": namespace, "name": name, "canonical_matches": 0,
              "canonical_total": len(pairs), "canonical_results": [],
              "generated_disagreements": 0, "first_counterexample": None}
        for key, (namespace, name, _) in rivals.items()
    }
    for pair in pairs:
        identity = _canonical_identity(pair)
        try:
            intended = _predict(module._predict, pair["input"], policy="intended")
            if intended != pair["output"]:
                report["errors"].append({"phase": "canonical_mirror", **identity,
                                         "input": pair["input"], "expected": pair["output"],
                                         "actual": intended})
            else:
                report["canonical_mirror_matches"] += 1
        except Exception as exc:
            report["errors"].append({"phase": "canonical_mirror", **identity, "error": str(exc)})
        for key, (_, _, solve) in rivals.items():
            entry = report["rivals"][key]
            try:
                prediction = _predict(solve, pair["input"])
                matches = prediction == pair["output"]
                entry["canonical_matches"] += int(matches)
                entry["canonical_results"].append({**identity, "matches": matches,
                                                    "prediction_sha256": _digest(prediction)})
                if not matches and "first_canonical_mismatch" not in entry:
                    entry["first_canonical_mismatch"] = {
                        **identity, "input": pair["input"], "canonical_output": pair["output"],
                        "rival_output": prediction,
                    }
            except Exception as exc:
                report["errors"].append({"phase": "canonical_rival", "rival": key,
                                         **identity, "error": str(exc)})
    for key, entry in report["rivals"].items():
        entry["fits_all_canonical"] = entry["canonical_matches"] == len(pairs)
        if entry["namespace"] == "CANONICAL_SHORTCUTS" and not entry["fits_all_canonical"]:
            report["errors"].append({"phase": "canonical_shortcut_fit", "rival": key,
                                     "error": "Declared canonical shortcut does not fit all labeled canonical pairs"})

    report["witnesses"] = {name: {"firings": 0, "evaluated": 0, "first_firing": None}
                           for name in witnesses}
    report["per_band"] = {}
    all_input_hashes = set()
    for band in args.bands:
        stats = {"attempted": args.samples, "generated": 0, "unique_inputs": 0,
                 "witness_firings": Counter(), "witness_evaluated": Counter(),
                 "rival_disagreements": Counter()}
        seen = set()
        for sample_index in range(args.start, args.start + args.samples):
            context = {"seed": args.seed, "sample_index": sample_index, "difficulty": band}
            try:
                grid = normalize_grid(module.generate(args.seed, sample_index, difficulty=band))
                prediction = _predict(module._predict, grid, policy="intended")
            except Exception as exc:
                report["errors"].append({"phase": "generation_or_mirror", **context, "error": str(exc)})
                continue
            stats["generated"] += 1
            seen.add(_digest(grid))
            all_input_hashes.add(_digest(grid))
            for name, predicate in witnesses.items():
                try:
                    fired = predicate(deepcopy(grid))
                    if type(fired) is not bool:
                        raise TypeError(f"Witness must return bool, got {type(fired).__name__}")
                    entry = report["witnesses"][name]
                    entry["evaluated"] += 1
                    stats["witness_evaluated"][name] += 1
                    if fired:
                        entry["firings"] += 1
                        stats["witness_firings"][name] += 1
                        if entry["first_firing"] is None:
                            entry["first_firing"] = _case(grid, prediction, **context)
                except Exception as exc:
                    report["errors"].append({"phase": "witness", "witness": name,
                                             **context, "error": str(exc)})
            for key, (_, _, solve) in rivals.items():
                try:
                    rival_output = _predict(solve, grid)
                    if rival_output != prediction:
                        entry = report["rivals"][key]
                        entry["generated_disagreements"] += 1
                        stats["rival_disagreements"][key] += 1
                        if entry["first_counterexample"] is None:
                            entry["first_counterexample"] = {
                                **_case(grid, prediction, **context), "rival_output": rival_output,
                                "rival_output_sha256": _digest(rival_output),
                            }
                except Exception as exc:
                    report["errors"].append({"phase": "generated_rival", "rival": key,
                                             **context, "error": str(exc)})
        stats["unique_inputs"] = len(seen)
        stats["witness_rates"] = {
            name: stats["witness_firings"][name] / stats["witness_evaluated"][name]
            if stats["witness_evaluated"][name] else None for name in witnesses
        }
        stats["witness_firings"] = {name: stats["witness_firings"][name] for name in witnesses}
        stats["witness_evaluated"] = {name: stats["witness_evaluated"][name] for name in witnesses}
        stats["rival_disagreements"] = {key: stats["rival_disagreements"][key] for key in rivals}
        report["per_band"][band] = stats
    report["unique_inputs_overall"] = len(all_input_hashes)
    for name, entry in report["witnesses"].items():
        entry["rate"] = entry["firings"] / entry["evaluated"] if entry["evaluated"] else None
        if not entry["firings"]:
            report["coverage_gaps"].append(f"Witness never fired: {name}")
    for key, entry in report["rivals"].items():
        if (entry["namespace"] == "CANONICAL_SHORTCUTS" and entry["fits_all_canonical"]
                and entry["first_counterexample"] is None):
            report["coverage_gaps"].append(f"No generated Python counterexample for canonical shortcut: {key}")
    for path, before in source_hashes.items():
        if _file_digest(path) != before:
            report["errors"].append({"phase": "source_changed_during_probe", "path": path})
    report["status"] = ("failed" if report["errors"] else
                        "coverage_gaps" if report["coverage_gaps"] else "provisional_evidence_complete")
    return report, 2 if report["errors"] else 1 if report["coverage_gaps"] else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--start", type=int, default=0, help="First sample index (default: 0)")
    parser.add_argument("--samples", type=int, default=100, help="Draws per band (default: 100)")
    parser.add_argument("--bands", nargs="+", choices=("easy", "medium", "hard"),
                        default=["easy", "medium", "hard"])
    parser.add_argument("--out", type=Path, required=True, help="New JSON evidence path; existing files are refused")
    args = parser.parse_args(argv)
    if args.samples < 1 or args.start < 0:
        parser.error("--samples must be positive and --start must be nonnegative")
    if len(set(args.bands)) != len(args.bands):
        parser.error("--bands must not contain duplicates")
    if args.out.exists():
        parser.error(f"Output already exists: {args.out}")
    try:
        report, exit_code = _run(args)
    except Exception as exc:
        report, exit_code = {"schema": "874aa60956cc-python-semantic-probe-v1", "task_id": TASK_ID,
                             "status": "infrastructure_error", "errors": [f"{type(exc).__name__}: {exc}"]}, 2
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({"status": report["status"], "out": str(args.out.resolve()),
                      "errors": len(report.get("errors", [])),
                      "coverage_gaps": report.get("coverage_gaps", []),
                      "generated_labels": "provisional_python_only"}))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
