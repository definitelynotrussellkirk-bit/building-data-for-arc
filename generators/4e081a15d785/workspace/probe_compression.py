"""Source-bound compression evidence using the public Racket authority.

Authoring probe: never run during a blind solve. Python rivals are hypotheses,
not reference labels. This module does no work at import time.
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

TASK_ID = "4e081a15d785"
BANDS = ("easy", "medium", "hard")
HAND_WITNESSES = (
    ("local_equal_cells", [[1, 1, 2], [1, 1, 2], [1, 2, 2]]),
    ("nonadjacent_columns", [[1, 1, 2, 2, 1], [1, 1, 2, 2, 1]]),
)


def bootstrap():
    """Import public helpers from this source/runtime tree, without siblings."""
    for ancestor in Path(__file__).resolve().parents:
        for directory in (ancestor / "shared/runtime", ancestor / "src", ancestor):
            if ((directory / "reviewer_support.py").is_file()
                    or (directory / "arcpuzzles/__init__.py").is_file()
                    or (directory / "puzzle_generators/base.py").is_file()):
                if str(directory) not in sys.path:
                    sys.path.insert(0, str(directory))
    from reviewer_support import canonical_pairs, find_root, normalize_grid
    from arcpuzzles import Catalog
    return canonical_pairs, find_root, normalize_grid, Catalog


def load_generator(root):
    candidates = (root / f"generators/{TASK_ID}/generator.py",
                  root / f"puzzle_generators/per_puzzle/{TASK_ID}/generator.py",
                  root / f"puzzle_generators/per_puzzle/{TASK_ID}.py")
    source = next((path for path in candidates if path.is_file()), None)
    if source is None:
        raise FileNotFoundError(f"Selected generator not found under {root}")
    spec = importlib.util.spec_from_file_location(f"compression_probe_{TASK_ID}", source)
    if spec is None or spec.loader is None:
        raise ImportError(str(source))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module, source


def digest(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def accepted(result):
    if type(result) is bool:
        return result
    if isinstance(result, (list, tuple)):
        return not result
    raise TypeError(f"Invalid validation result {result!r}")


def run(args, report):
    canonical_pairs, find_root, normalize_grid, Catalog = bootstrap()
    root = find_root(__file__)
    module, source = load_generator(root)
    catalog = Catalog(Path(args.library).resolve() if args.library else root)
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    report.update(source={"generator_path": str(source), "generator_sha256": source_hash,
                          "version": getattr(module, "VERSION", None)},
                  schedule={"period": getattr(module, "LESSON_SCHEDULE_PERIOD", None)},
                  canonical=[], generated_witnesses={}, hand_witnesses=[], authority_batches=[],
                  bands={}, missing_contract=[], missing_witnesses=[])
    rivals = {}
    shortcuts = getattr(module, "CANONICAL_SHORTCUTS", {})
    for namespace in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS"):
        declaration = getattr(module, namespace, None)
        if declaration is None:
            report["missing_contract"].append(namespace)
            continue
        if not isinstance(declaration, dict):
            raise TypeError(f"{namespace} must be a mapping")
        for name, solve in declaration.items():
            if not isinstance(name, str) or not callable(solve):
                raise TypeError(f"Invalid rival declaration {namespace}.{name}")
            # Preserve namespace identities even when names coincide.
            rivals[f"{namespace}.{name}"] = solve
    for hook in ("strict_canonical_like", "observe_overrides", "schedule_profile"):
        if not callable(getattr(module, hook, None)):
            report["missing_contract"].append(hook)
    pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    if not pairs:
        raise ValueError("No labeled canonical pairs")
    report["canonical_pair_count"] = len(pairs)
    for pair in pairs:
        identity = {key: pair[key] for key in ("variant", "split", "pair_index")}
        row = {**identity, "shortcut_fit": {}}
        strict = getattr(module, "strict_canonical_like", None)
        if callable(strict):
            row["strict_accepted"] = accepted(strict(deepcopy(pair["input"])))
            if not row["strict_accepted"]:
                report["errors"].append({"kind": "canonical_strict_rejected", **identity})
        for name, solve in shortcuts.items():
            try:
                prediction = solve(deepcopy(pair["input"]))
                fits = prediction == pair["output"]
                row["shortcut_fit"][name] = fits
                if not fits:
                    report["errors"].append({"kind": "canonical_shortcut_misdeclaration",
                                              "name": name, **identity, "input": pair["input"],
                                              "reference": pair["output"], "rival": prediction})
            except Exception as exc:
                report["errors"].append({"kind": "canonical_rival_error", "name": name,
                                          **identity, "error": f"{type(exc).__name__}: {exc}"})
        report["canonical"].append(row)
    records = []
    summaries = {}
    for band in BANDS:
        summaries[band] = {"attempted": args.seeds * args.samples, "generated": 0,
                           "reference_labeled": 0, "strict_count": 0, "strict_checked": 0,
                           "input_shapes": Counter(), "output_shapes": Counter(),
                           "observed_controls": {}, "profiles": Counter(), "unique": set()}
        summary = summaries[band]
        for seed in range(args.seeds):
            for index in range(args.samples):
                identity = {"seed": seed, "sample_index": index, "difficulty": band}
                try:
                    grid = normalize_grid(module.generate(seed, index, difficulty=band))
                    validation = module.self_check(deepcopy(grid), difficulty=band)
                    if not accepted(validation):
                        raise ValueError(f"self_check rejected: {validation}")
                    record = {**identity, "kind": "generated", "input": grid}
                    summary["generated"] += 1
                    summary["unique"].add(digest(grid))
                    summary["input_shapes"][f"{len(grid)}x{len(grid[0])}"] += 1
                    strict = getattr(module, "strict_canonical_like", None)
                    if callable(strict):
                        record["strict_accepted"] = accepted(strict(deepcopy(grid)))
                        summary["strict_checked"] += 1
                        summary["strict_count"] += int(record["strict_accepted"])
                    observe = getattr(module, "observe_overrides", None)
                    if callable(observe):
                        controls = observe(deepcopy(grid))
                        if not isinstance(controls, dict):
                            raise TypeError("observe_overrides must return a mapping")
                        record["observed_controls"] = controls
                        for name, value in controls.items():
                            summary["observed_controls"].setdefault(name, Counter())[str(value)] += 1
                    profile = getattr(module, "schedule_profile", None)
                    if callable(profile):
                        record["profile"] = str(profile(seed, index, difficulty=band))
                        summary["profiles"][record["profile"]] += 1
                    records.append(record)
                except Exception as exc:
                    report["errors"].append({"kind": "generation_validation_error", **identity,
                                              "error": f"{type(exc).__name__}: {exc}"})
    if args.hand_witness:
        records.extend({"kind": "hand_authored_diagnostic", "name": name, "input": grid}
                       for name, grid in HAND_WITNESSES)
    for offset in range(0, len(records), 64):
        batch = records[offset:offset + 64]
        try:
            applied = catalog.apply(TASK_ID, [record["input"] for record in batch],
                                    reference="canonical", allow_unapproved=True, timeout=args.timeout)
            identity = {key: applied[key] for key in ("generator_sha256", "executed_rule_hash",
                        "catalog_rule_hash", "rule_text_sha256", "rule_hash_matches_catalog")}
            report["authority_batches"].append({"offset": offset, "count": len(batch), **identity})
            if identity["generator_sha256"] != source_hash:
                raise ValueError("Catalog applied a different generator source")
            if not identity["rule_hash_matches_catalog"]:
                raise ValueError("Executed rule differs from catalog authority")
            if report.get("authority_identity") not in (None, identity):
                raise ValueError("Authority identity changed between batches")
            report["authority_identity"] = identity
            if len(applied["results"]) != len(batch):
                raise ValueError("Authority returned wrong result count")
        except Exception as exc:
            failure = {"kind": "authority_batch_error", "offset": offset,
                       "error": f"{type(exc).__name__}: {exc}", "cases": batch}
            if isinstance(getattr(exc, "run", None), dict):
                failure["process_receipt"] = exc.run
            report["errors"].append(failure)
            continue
        for record, result in zip(batch, applied["results"], strict=True):
            if not result["valid_output"] or result.get("error"):
                report["errors"].append({"kind": "authority_input_error", **record, "result": result})
                continue
            output = normalize_grid(result["output"])
            predictions = {}
            for name, solve in rivals.items():
                try:
                    predictions[name] = solve(deepcopy(record["input"]))
                except Exception as exc:
                    report["errors"].append({"kind": "generated_rival_error", "name": name,
                                              **record, "error": f"{type(exc).__name__}: {exc}"})
            if record["kind"] == "generated":
                summary = summaries[record["difficulty"]]
                summary["reference_labeled"] += 1
                summary["output_shapes"][f"{len(output)}x{len(output[0])}"] += 1
                controls = record.get("observed_controls", {})
                expected = {"grid_h": len(record["input"]), "grid_w": len(record["input"][0]),
                            "base_color_count": len({c for row in record["input"] for c in row}),
                            "n_duplicates": len(record["input"]) - len(output),
                            "n_column_duplicates": len(record["input"][0]) - len(output[0])}
                for name, value in expected.items():
                    if name in controls and controls[name] != value:
                        report["errors"].append({"kind": "observed_control_mismatch", **record,
                                                  "control": name, "expected": value,
                                                  "observed": controls[name], "reference": output})
                for name, prediction in predictions.items():
                    if prediction != output and name not in report["generated_witnesses"]:
                        report["generated_witnesses"][name] = {**record, "reference": output,
                                                              "rival": prediction}
            else:
                report["hand_witnesses"].append({**record, "reference": output,
                                                "rival_predictions": predictions,
                                                "refuted": [name for name, pred in predictions.items()
                                                            if pred != output]})
    for band, summary in summaries.items():
        summary["unique_input_count"] = len(summary.pop("unique"))
        checked = summary["strict_checked"]
        summary["strict_fraction"] = summary["strict_count"] / checked if checked else None
        report["bands"][band] = summary
    report["missing_witnesses"] = sorted(set(rivals) - set(report["generated_witnesses"]))
    if hashlib.sha256(source.read_bytes()).hexdigest() != source_hash:
        report["errors"].append({"kind": "source_changed_during_probe"})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=2, help="Seeds 0 through N-1")
    parser.add_argument("--samples", type=int, default=8, help="Consecutive indices starting at zero")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--library", help="Catalog root, needed for a standalone copied runtime")
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("--hand-witness", action="store_true")
    parser.add_argument("--require-witness", action="store_true",
                        help="Fail if any declared rival lacks a generated counterexample or contract is missing")
    args = parser.parse_args(argv)
    if args.seeds < 1 or args.samples < 1:
        parser.error("--seeds and --samples must be positive")
    if args.out.exists():
        parser.error("--out must be a new path; preserve earlier source-bound evidence")
    report = {"schema": "arcpuzzles-task-compression-probe-v1", "task_id": TASK_ID,
              "invocation": {"argv": [sys.executable, *sys.argv], "cwd": str(Path.cwd())},
              "settings": {"seeds": args.seeds, "samples": args.samples,
                           "bands": list(BANDS), "hand_witness": args.hand_witness,
                           "require_witness": args.require_witness, "batch_limit": 64},
              "reference_basis": "Public Catalog.apply canonical Racket execution; no Python reference mirror",
              "errors": []}
    try:
        run(args, report)
    except Exception as exc:
        report["errors"].append({"kind": "probe_error", "error": f"{type(exc).__name__}: {exc}"})
    missing = report.get("missing_witnesses", []) or report.get("missing_contract", [])
    exit_code = 2 if report["errors"] else (1 if args.require_witness and missing else 0)
    report["status"] = "ERROR" if report["errors"] else ("MISSING_COVERAGE" if missing else "PASS")
    report["exit_code"] = exit_code
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], "out": str(args.out),
                      "errors": len(report["errors"]), "missing_witnesses": report.get("missing_witnesses", []),
                      "missing_contract": report.get("missing_contract", [])}))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
