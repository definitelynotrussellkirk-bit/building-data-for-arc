#!/usr/bin/env python3
"""Finite Python diagnostics for the selected downward-column gravity sampler.

Run from a library or copied runtime; --source can select a retained baseline.
Each diagnostic window has --train demonstrations and one query, with every pair
held out in turn. By default, --train uses the selected generator's positive
integer EXAMPLES_NEEDED declaration, falling back to 3 when absent or invalid.
This never invokes Racket, the production materializer, assignment or audit draws.
All generated labels come from an independent adjacent-swap implementation.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import shlex
import sys

sys.dont_write_bytecode = True


TASK_ID = "2a43e4f3a796"
BANDS = ("easy", "medium", "hard")
HERE = Path(__file__).resolve()

# Bootstrap the public portable helper from this tree, never a sibling checkout.
for _ancestor in HERE.parents:
    _support = next((p for p in (_ancestor / "reviewer_support.py",
                                 _ancestor / "shared/runtime/reviewer_support.py")
                     if p.is_file()), None)
    if _support is not None:
        sys.path.insert(0, str(_support.parent))
        break
else:
    raise RuntimeError("Cannot locate this tree's reviewer_support.py")

from reviewer_support import canonical_pairs, canonical_path, find_root, normalize_grid

ROOT = find_root(__file__)


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":"),
                                     sort_keys=True).encode()).hexdigest()


def adjacent_swap_gravity(grid):
    """Repeated adjacent downward swaps; no extraction or packing of columns."""
    out = normalize_grid(deepcopy(grid))
    h, w = len(out), len(out[0])
    for _ in range(h):
        changed = False
        for r in range(h - 2, -1, -1):
            for c in range(w):
                if out[r][c] != 0 and out[r + 1][c] == 0:
                    out[r + 1][c], out[r][c] = out[r][c], 0
                    changed = True
        if not changed:
            return out
    raise AssertionError("Adjacent-swap gravity failed to settle within h passes")


def load_generator(source):
    spec = importlib.util.spec_from_file_location("gravity_distribution_subject", source)
    if spec is None or spec.loader is None:
        raise ValueError(f"Cannot import generator: {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    if getattr(module, "TASK_ID", TASK_ID) != TASK_ID:
        raise ValueError("Selected source declares a different TASK_ID")
    if not callable(getattr(module, "generate", None)):
        raise ValueError("Selected source has no callable generate")
    return module


def declarations(module):
    rivals, contracts, errors = {}, {}, []
    for namespace in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS"):
        raw = getattr(module, namespace, None)
        info = {"present": hasattr(module, namespace), "names": []}
        if raw is not None:
            if not isinstance(raw, dict):
                errors.append(f"{namespace}: expected a dict, got {type(raw).__name__}")
            else:
                for name, fn in raw.items():
                    if not isinstance(name, str) or not callable(fn):
                        errors.append(f"{namespace}[{name!r}]: expected a string name and callable")
                        continue
                    qualified = f"{namespace}.{name}"
                    rivals[qualified] = fn
                    info["names"].append(name)
        info["names"].sort()
        info["callable_count"] = len(info["names"])
        contracts[namespace] = info
    return rivals, contracts, errors


def predict(fn, grid):
    supplied = deepcopy(grid)
    try:
        result = normalize_grid(fn(supplied))
        if supplied != grid:
            raise ValueError("Rival mutated its input")
        return {"output": result}
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}"}


def check_input(module, grid, band=None):
    fn = getattr(module, "self_check", None)
    if not callable(fn):
        return ["self_check contract absent"]
    try:
        supplied = deepcopy(grid)
        result = fn(supplied, difficulty=band)
        if supplied != grid:
            return ["self_check mutated its input"]
        if not isinstance(result, list) or any(not isinstance(v, str) for v in result):
            return [f"self_check returned {type(result).__name__}; expected list[str]"]
        return result
    except Exception as exc:
        return [f"self_check raised {type(exc).__name__}: {exc}"]


def source_rules():
    """Hash the selected task's canonical program text; do not execute it."""
    identities = []
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                program = row.get("program_solution")
                if not isinstance(program, str) or not program:
                    raise ValueError("Canonical row has no program_solution source")
                sha = hashlib.sha256(program.encode()).hexdigest()
                rule_hash = hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12]
                identities.append({"variant": len(identities),
                                   "program_sha256": sha, "rule_hash": rule_hash})
    if not identities:
        raise ValueError("No canonical rule source was found")
    return identities


def canonical_report(rivals):
    result = {"labeled_pairs": 0, "oracle_matches": 0, "errors": [], "rivals": {}}
    try:
        pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    except Exception as exc:
        result["errors"].append(f"{type(exc).__name__}: {exc}")
        result["status"] = "canonical_read_error"
        return result
    result["labeled_pairs"] = len(pairs)
    result["pairs_sha256"] = digest(pairs)
    for pair in pairs:
        if adjacent_swap_gravity(pair["input"]) == pair["output"]:
            result["oracle_matches"] += 1
        else:
            result["errors"].append("Oracle disagrees with canonical "
                                    f"{pair['variant']}/{pair['split']}/{pair['pair_index']}")
    for name, rival in rivals.items():
        counts = {"matches": 0, "mismatches": 0, "errors": 0, "error_examples": []}
        for pair in pairs:
            prediction = predict(rival, pair["input"])
            if "error" in prediction:
                counts["errors"] += 1
                if len(counts["error_examples"]) < 3:
                    counts["error_examples"].append({
                        "variant": pair["variant"], "split": pair["split"],
                        "pair_index": pair["pair_index"], "error": prediction["error"]})
            else:
                counts["matches" if prediction["output"] == pair["output"] else "mismatches"] += 1
        counts["fits_all"] = bool(pairs) and counts["matches"] == len(pairs) and counts["errors"] == 0
        result["rivals"][name] = counts
    result["status"] = "contract_absent" if not rivals else "scored"
    return result


# Expected outputs are literal, authored fixtures; the independent oracle checks
# them before they are offered for separate public Racket apply verification.
WITNESSES = (
    ("combined", [[5,5],[1,5],[5,5],[0,0],[5,0],[5,2],[5,0]],
     [[0,0],[5,0],[1,0],[5,5],[5,5],[5,5],[5,2]]),
    ("all_zero", [[0,0],[0,0]], [[0,0],[0,0]]),
    ("singleton", [[3]], [[3]]),
    ("floating_gray_singleton", [[5,0],[0,0],[0,0]], [[0,0],[0,0],[5,0]]),
    ("full_grid", [[1,2,3],[4,5,6]], [[1,2,3],[4,5,6]]),
    ("already_settled", [[0,0],[1,0],[2,3]], [[0,0],[1,0],[2,3]]),
    ("one_row", [[2,0,5,0]], [[2,0,5,0]]),
    ("one_column", [[5],[0],[2],[0]], [[0],[0],[5],[2]]),
)


def witness_report(module, rivals):
    result = []
    for name, inp, expected in WITNESSES:
        if adjacent_swap_gravity(inp) != expected:
            raise AssertionError(f"Literal fixture disagrees with oracle: {name}")
        result.append({"name": name, "input": inp, "expected_output": expected,
                       "oracle_matches_literal": True,
                       "self_check_errors": check_input(module, inp),
                       "rival_predictions": {key: predict(fn, inp) for key, fn in rivals.items()}})
    return result


def sample(module, seed, index, band):
    row = {"sample_index": index, "errors": []}
    try:
        grid = normalize_grid(module.generate(seed, index, difficulty=band))
        row.update(input=grid, input_sha256=digest(grid), output=adjacent_swap_gravity(grid))
        row["self_check_errors"] = check_input(module, grid, band)
        row["errors"].extend(row["self_check_errors"])
    except Exception as exc:
        row["errors"].append(f"generate/oracle raised {type(exc).__name__}: {exc}")
    profile = getattr(module, "schedule_profile", None)
    if callable(profile):
        try:
            value = profile(seed, index, difficulty=band)
            hash(value)
            row["profile"] = value if isinstance(value, str) else repr(value)
        except Exception as exc:
            row["errors"].append(f"schedule_profile raised {type(exc).__name__}: {exc}")
    else:
        row["profile"] = "contract_absent"
    return row


def distribution_and_windows(module, rivals, seeds, indices, train):
    pair_count = train + 1
    bands = {}
    window_totals = Counter()
    rival_totals = {name: Counter() for name in rivals}
    smallest, smallest_key = None, None
    error_examples = []

    def retain_failure(kind, band, seed, start, rows, query, name=None, predictions=None):
        nonlocal smallest, smallest_key
        if not all("input" in row and "output" in row for row in rows):
            return
        sizes = [len(row["input"]) * len(row["input"][0]) for row in rows]
        key = (sum(sizes), max(sizes), BANDS.index(band), seed, start, query, name or "")
        if smallest_key is None or key < smallest_key:
            smallest_key = key
            smallest = {"kind": kind, "band": band, "seed": seed, "start": start,
                        "sample_indices": [row["sample_index"] for row in rows],
                        "train_count": train, "pair_count": pair_count,
                        "query_pair_index": query,
                        "demo_pair_indices": [i for i in range(pair_count) if i != query],
                        "size_order_key": list(key), "rival": name,
                        "pairs": [{k: row[k] for k in ("sample_index", "input_sha256", "input", "output", "errors")}
                                  for row in rows]}
            if predictions is not None:
                smallest["rival_predictions"] = predictions

    for band in BANDS:
        counts, profiles, reasons, unique = Counter(), Counter(), Counter(), set()
        for seed in range(seeds):
            # Extra indices are exclusively window evidence, not marginal draws.
            rows = [sample(module, seed, i, band) for i in range(indices + pair_count - 1)]
            predictions = {}
            for row in rows:
                if row["errors"]:
                    window_totals["unique_sample_errors"] += 1
                    if len(error_examples) < 5:
                        error_examples.append({"band": band, "seed": seed,
                                               "sample_index": row["sample_index"], "errors": row["errors"]})
                if "input" in row:
                    predictions[row["sample_index"]] = {
                        name: predict(fn, row["input"]) for name, fn in rivals.items()}
            for row in rows[:indices]:
                counts["attempted_samples"] += 1
                profiles[row.get("profile", "profile_error")] += 1
                if row["errors"]:
                    counts["samples_with_errors"] += 1
                    reasons.update(row["errors"])
                if "input" not in row:
                    counts["generation_or_oracle_failures"] += 1
                    continue
                grid = row["input"]
                counts["valid_grid_samples"] += 1
                unique.add(row["input_sha256"])
                h, w = len(grid), len(grid[0])
                columns = [sum(grid[r][c] != 0 for r in range(h)) for c in range(w)]
                counts["column_denominator"] += w
                counts["bottom_occupied_inputs"] += int(any(grid[-1]))
                for label, predicate in (("singleton", lambda n: n == 1),
                                         ("long_gt5", lambda n: n > 5),
                                         ("full", lambda n: n == h),
                                         ("empty", lambda n: n == 0)):
                    number = sum(predicate(n) for n in columns)
                    counts[f"{label}_columns"] += number
                    counts[f"inputs_with_{label}_columns"] += int(number > 0)
                colors = Counter(v for line in grid for v in line)
                modes = [v for v, n in colors.items() if n == max(colors.values())]
                counts["nonzero_unique_mode_inputs"] += int(len(modes) == 1 and modes[0] != 0)
                counts["tied_mode_inputs"] += int(len(modes) > 1)
                counts["self_check_evaluated"] += 1
                counts["self_check_failures"] += int(bool(row.get("self_check_errors")))
            for start in range(indices):
                window = rows[start:start + pair_count]
                window_totals["windows"] += 1
                window_totals["requested_rotations"] += pair_count
                if any(row["errors"] for row in window):
                    window_totals["windows_with_sample_errors"] += 1
                    retain_failure("sample_error", band, seed, start, window, 0)
                if not all("input" in row and "output" in row for row in window):
                    window_totals["unscored_incomplete_windows"] += 1
                    continue
                window_totals["complete_windows"] += 1
                if not rivals:
                    window_totals["unscored_contract_absent_windows"] += 1
                    continue
                window_totals["scored_rotations"] += pair_count
                ambiguous_positions, error_positions = set(), set()
                for name in rivals:
                    values = [predictions[row["sample_index"]][name] for row in window]
                    if any("error" in value for value in values):
                        rival_totals[name]["error_rotations"] += pair_count
                        error_positions.update(range(pair_count))
                        retain_failure("rival_error", band, seed, start, window, 0, name, values)
                        continue
                    matches = [value["output"] == row["output"] for value, row in zip(values, window)]
                    for query in range(pair_count):
                        demo_fit = all(value for i, value in enumerate(matches) if i != query)
                        state = "refuted" if not demo_fit else ("survived_all" if matches[query] else "ambiguous")
                        rival_totals[name][state] += 1
                        if state == "ambiguous":
                            ambiguous_positions.add(query)
                            retain_failure("ambiguity", band, seed, start, window, query, name, values)
                window_totals["ambiguous_rotations"] += len(ambiguous_positions)
                window_totals["rival_error_rotations"] += len(error_positions)
        for field in ("attempted_samples", "valid_grid_samples", "samples_with_errors",
                      "generation_or_oracle_failures", "column_denominator", "bottom_occupied_inputs",
                      "singleton_columns", "long_gt5_columns", "full_columns", "empty_columns",
                      "inputs_with_singleton_columns", "inputs_with_long_gt5_columns",
                      "inputs_with_full_columns", "inputs_with_empty_columns",
                      "nonzero_unique_mode_inputs", "tied_mode_inputs",
                      "self_check_evaluated", "self_check_failures"):
            counts.setdefault(field, 0)
        bands[band] = {**dict(counts), "unique_inputs": len(unique),
                       "profiles": dict(sorted(profiles.items())),
                       "error_reasons": dict(reasons.most_common(10))}
    for name in ("unique_sample_errors", "windows_with_sample_errors", "unscored_incomplete_windows",
                 "scored_rotations", "ambiguous_rotations", "rival_error_rotations"):
        window_totals.setdefault(name, 0)
    windows = {"status": "contract_absent" if not rivals else "scored",
               "scope": "Direct generate calls and Python labels; no production materialization, deduplication, rejection, or Racket execution",
               "train_count": train, "pair_count": pair_count,
               "seeds": {"first": 0, "last": seeds - 1, "count": seeds},
               "sample_indices_called_per_seed_and_band": list(range(indices + pair_count - 1)),
               "windows_by_start": [{"start": i, "sample_indices": list(range(i, i + pair_count))} for i in range(indices)],
               "query_pair_positions": list(range(pair_count)),
               "reuse": "Each generated index is reused across its overlapping windows; predictions are pure diagnostic calls",
               "counts": dict(window_totals),
               "rival_rotation_counts": {k: dict(v) for k, v in rival_totals.items()},
               "error_examples": error_examples,
               "failure_selection": "Minimum (total cells, largest pair cells, band order, seed, start, query position, rival name) among complete failures",
               "smallest_complete_failure_witness": smallest}
    return bands, windows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--source", type=Path, help="Absolute generator.py path; default is this tree's selected source")
    parser.add_argument("--seeds", type=int, default=100)
    parser.add_argument("--indices", type=int, default=4, help="Marginal indices and diagnostic window starts, beginning at zero")
    parser.add_argument("--train", type=int,
                        help="Demonstrations per window; default: generator.EXAMPLES_NEEDED, or 3 when absent or invalid")
    args = parser.parse_args()
    if args.seeds < 1 or args.indices < 1:
        parser.error("--seeds and --indices must both be positive")
    if args.train is not None and args.train < 1:
        parser.error("--train must be positive")
    if args.source is not None and not args.source.is_absolute():
        parser.error("--source must be an absolute path")
    selected = next((p for p in (ROOT / "generators" / TASK_ID / "generator.py",
                                 ROOT / "puzzle_generators/per_puzzle" / TASK_ID / "generator.py")
                     if p.is_file()), None)
    source = args.source.resolve() if args.source is not None else selected
    if source is None or not source.is_file():
        parser.error("Cannot locate the requested generator source")
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    module = load_generator(source)
    if hashlib.sha256(source.read_bytes()).hexdigest() != source_sha:
        raise RuntimeError("Generator source changed during import; rerun after edits finish")
    declared_train = getattr(module, "EXAMPLES_NEEDED", None)
    if args.train is not None:
        train, train_basis = args.train, "explicit --train"
    elif type(declared_train) is int and declared_train > 0:
        train, train_basis = declared_train, "generator.EXAMPLES_NEEDED"
    else:
        train, train_basis = 3, "fallback: generator has no valid positive integer EXAMPLES_NEEDED"
    pair_count = train + 1
    rivals, contracts, declaration_errors = declarations(module)
    canonical = canonical_report(rivals)
    rule_sources = source_rules()
    rule_pins = sorted({item["rule_hash"] for item in rule_sources})
    declared_pin = getattr(module, "RULE_HASH", None)
    identity_errors = []
    if declared_pin is not None and declared_pin not in rule_pins:
        identity_errors.append("Generator RULE_HASH does not match the canonical program hash")
    bands, windows = distribution_and_windows(module, rivals, args.seeds, args.indices, train)
    witnesses = witness_report(module, rivals)
    if hashlib.sha256(source.read_bytes()).hexdigest() != source_sha:
        identity_errors.append("Generator source changed during this probe; rerun after edits finish")
    witness_prediction_errors = sum("error" in prediction for row in witnesses
                                    for prediction in row["rival_predictions"].values())
    errors = (len(declaration_errors) + len(identity_errors) + len(canonical["errors"])
              + sum(row["errors"] for row in canonical["rivals"].values())
              + windows["counts"]["unique_sample_errors"] + windows["counts"]["rival_error_rotations"]
              + witness_prediction_errors)
    ambiguities = windows["counts"]["ambiguous_rotations"]
    status = ("errors" if errors else "ambiguities_found" if ambiguities else
              "contract_absent" if not rivals else "no_ambiguity_found_against_declared_rivals")
    command = [sys.executable, str(HERE), "--out", str(args.out.resolve()),
               "--seeds", str(args.seeds), "--indices", str(args.indices), "--train", str(train)]
    if args.source is not None:
        command.extend(("--source", str(source)))
    report = {
        "schema": "gravity-distribution-diagnostic-v1", "task_id": TASK_ID, "status": status,
        "evidence_type": "Python diagnostic only; finite declared-rival evidence, not a production-sampler or Racket-label claim",
        "root": str(ROOT), "source_path": str(source),
        "source_selection": "explicit_source" if args.source is not None else "selected_source",
        "source_sha256": source_sha,
        "probe_path": str(HERE), "probe_sha256": hashlib.sha256(HERE.read_bytes()).hexdigest(),
        "rule_pin": rule_pins[0] if len(rule_pins) == 1 else None,
        "rule_pin_basis": "SHA-256 prefix of canonical program text; not executed by this probe",
        "generator_declared_rule_pin": declared_pin, "canonical_rule_sources": rule_sources,
        "identity_errors": identity_errors, "command": shlex.join(command), "argv": command,
        "generation": {"call": "generate(seed, sample_index, difficulty=band)", "overrides": {},
                       "bands": list(BANDS), "seeds": args.seeds, "indices": args.indices,
                       "requested_train_count": args.train, "train_count": train,
                       "train_count_basis": train_basis, "pair_count": pair_count,
                       "marginal_sample_indices": list(range(args.indices)),
                       "marginal_attempts_per_band": args.seeds * args.indices},
        "contracts": contracts, "declaration_errors": declaration_errors,
        "canonical": canonical, "per_band": bands, "diagnostic_windows": windows,
        "witness_summary": {"cases": len(witnesses), "literal_outputs_checked": len(witnesses),
                            "self_check_failures": sum(bool(row["self_check_errors"]) for row in witnesses),
                            "rival_prediction_errors": witness_prediction_errors,
                            "scope": "Authored endpoint inputs, separate from ordinary sample denominators"},
        "witnesses": witnesses,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.out.with_name(args.out.name + ".tmp")
    temporary.write_text(json.dumps(report, separators=(",", ":"), sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(args.out)
    print(json.dumps({"status": status, "out": str(args.out.resolve()),
                      "source_sha256": report["source_sha256"], "rule_pin": report["rule_pin"],
                      "train_count": train, "train_count_basis": train_basis, "pair_count": pair_count,
                      "marginal_attempts_per_band": args.seeds * args.indices,
                      "window_counts": windows["counts"]}, sort_keys=True))
    return 2 if errors else 1 if ambiguities else 0


if __name__ == "__main__":
    raise SystemExit(main())
