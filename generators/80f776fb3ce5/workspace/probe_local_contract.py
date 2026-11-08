"""Exhaustive local predicate probe, labelled through public Catalog.apply.

Run via review.py run python3 generators/80f776fb3ce5/workspace/probe_local_contract.py
--out ../checks/local-contract.json. This is authoring evidence, never solve evidence.
All 512 binary 3x3 neighborhoods are tested, with compact fixed-color extensions.
Finite local rival refutation does not establish lesson identifiability or generation support.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys

from reviewer_support import canonical_pairs, canonical_path, find_root

TASK_ID = "80f776fb3ce5"
NAMESPACES = ("SEMANTIC_RIVALS", "LESSON_COMPETITORS", "CANONICAL_SHORTCUTS")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def cases(binary_only=False):
    result = [{"kind": "binary", "input": [list(bits[i:i + 3]) for i in (0, 3, 6)]}
              for bits in itertools.product((0, 1), repeat=9)]
    if not binary_only:
        plus = [[0, 1, 0], [1, 0, 1], [0, 1, 0]]
        for color in range(2, 10):
            grid = deepcopy(plus); grid[1][1] = color
            result.append({"kind": "occupied_center", "input": grid})
            for r, c in ((0, 1), (1, 0), (1, 2), (2, 1)):
                grid = deepcopy(plus); grid[r][c] = color
                result.append({"kind": "nonblue_arm", "input": grid})
            grid = deepcopy(plus)
            for r, c in ((0, 1), (1, 0), (1, 2), (2, 1)):
                grid[r][c] = color
            result.append({"kind": "nonblue_surround", "input": grid})
            grid = deepcopy(plus); grid[0][0] = color
            result.append({"kind": "diagonal_palette", "input": grid})
    return result


def expected(grid):
    """Independent predicate; never calls generator mirrors or rival functions."""
    out = deepcopy(grid)
    for r in range(1, len(grid) - 1):
        for c in range(1, len(grid[0]) - 1):
            if (grid[r][c] == 0 and grid[r - 1][c] == 1 and grid[r + 1][c] == 1
                    and grid[r][c - 1] == 1 and grid[r][c + 1] == 1):
                out[r][c] = 8
    return out


def declarations(generator):
    result = {}
    for namespace in NAMESPACES:
        mapping = getattr(generator, namespace, {})
        if not isinstance(mapping, dict):
            raise TypeError(f"{namespace} must be a dictionary")
        for name, predictor in mapping.items():
            if not isinstance(name, str) or not callable(predictor):
                raise TypeError(f"Invalid {namespace} declaration: {name!r}")
            result[f"{namespace}.{name}"] = predictor
    return result


def predict(predictor, grid):
    try:
        return predictor(deepcopy(grid)), None
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


def acceptance(generator, grid):
    try:
        reasons = generator.self_check(deepcopy(grid))
        if not isinstance(reasons, list) or any(not isinstance(r, str) for r in reasons):
            raise TypeError("self_check must return a list of strings")
        return {"accepted": not reasons, "reasons": reasons}
    except Exception as exc:
        return {"accepted": False, "error": f"{type(exc).__name__}: {exc}"}


def witness_key(item):
    grid = item["input"]
    return (len(grid) * len(grid[0]), sum(v != 0 for row in grid for v in row),
            tuple(v for row in grid for v in row))


def companion(grid):
    """Keep the local probe left of a separating column and an eligible plus."""
    return [list(row) + [0] + extra for row, extra in zip(
        grid, ([0, 1, 0], [1, 0, 1], [0, 1, 0]), strict=True)]


def apply_batches(catalog, grids, timeout):
    receipts, outputs = [], []
    for start in range(0, len(grids), 64):
        record = catalog.apply(TASK_ID, deepcopy(grids[start:start + 64]), timeout=timeout)
        rows = record.get("results", [])
        if len(rows) != len(grids[start:start + 64]):
            raise ValueError("Catalog.apply result count differs from request")
        if not record.get("rule_hash_matches_catalog"):
            raise ValueError("Executed rule differs from catalog authority")
        for row in rows:
            if row.get("error") is not None or row.get("output") is None:
                raise ValueError(f"Catalog.apply input failure: {row.get('error')}")
            outputs.append(row["output"])
        receipts.append({"start": start, "count": len(rows), "record": record})
    return outputs, receipts


def build_report(generator, catalog, source, root, *, binary_only=False, timeout=120):
    source_hash = sha(source.read_bytes())
    description = catalog.describe(TASK_ID)
    if description["generator_sha256"] != source_hash:
        raise ValueError("Catalog source identity differs from loaded generator")
    probes = cases(binary_only)
    grids = [item["input"] for item in probes]
    outputs, receipts = apply_batches(catalog, grids, timeout)
    for receipt in receipts:
        if receipt["record"]["generator_sha256"] != source_hash:
            raise ValueError("Authority receipt source identity changed")
    failures = []
    accepted = 0
    for index, (item, output) in enumerate(zip(probes, outputs, strict=True)):
        item.update(index=index, output=output, validator=acceptance(generator, item["input"]))
        accepted += item["validator"]["accepted"]
        wanted = expected(item["input"])
        if output != wanted:
            failures.append({"index": index, "input": item["input"], "actual": output,
                             "expected": wanted})
    canonical = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    if not canonical:
        raise ValueError("No labelled canonical pairs")
    scores, embeddings = {}, []
    for name, predictor in declarations(generator).items():
        canonical_fit, canonical_errors = 0, []
        for pair in canonical:
            prediction, error = predict(predictor, pair["input"])
            canonical_fit += error is None and prediction == pair["output"]
            if error:
                canonical_errors.append(error)
        refutations, errors = [], []
        for item in probes:
            prediction, error = predict(predictor, item["input"])
            if error:
                errors.append({"index": item["index"], "error": error})
            elif prediction != item["output"]:
                refutations.append({**item, "rival_output": prediction})
        witness = min(refutations, key=witness_key) if refutations else None
        scores[name] = {"canonical_fit": canonical_fit, "canonical_total": len(canonical),
                        "canonical_errors": canonical_errors, "local_refuted": len(refutations),
                        "local_total": len(probes), "local_errors": errors,
                        "minimal_witness": witness,
                        "minimality_policy": "minimum area, then nonzero cells, then row-major values within enumerated corpus"}
        if witness and not witness["validator"]["accepted"]:
            grid = companion(witness["input"])
            validation = acceptance(generator, grid)
            prediction, error = predict(predictor, grid)
            if validation["accepted"] and error is None:
                embeddings.append({"rival": name, "input": grid, "validator": validation,
                                   "rival_output": prediction})
    if embeddings:
        embedded_outputs, embedded_receipts = apply_batches(catalog, [e["input"] for e in embeddings], timeout)
        receipts.extend({**r, "corpus": "accepted_companions"} for r in embedded_receipts)
        for item, output in zip(embeddings, embedded_outputs, strict=True):
            item["output"] = output
            item["refutes"] = output != item["rival_output"]
            if output != expected(item["input"]):
                failures.append({"companion": item, "expected": expected(item["input"])})
            if item["refutes"]:
                scores[item["rival"]]["accepted_companion"] = item
    if sha(source.read_bytes()) != source_hash:
        raise ValueError("Generator changed during probe; rerun against stable final bytes")
    canonical_records = []
    for line in canonical_path(root).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            program = row["program_solution"]
            canonical_records.append({"record_sha256_without_newline": sha(line.encode()),
                                      "rule_text_sha256": sha(program.encode()),
                                      "normalized_rule_sha256": sha(" ".join(program.split()).encode())})
    return {"schema": "80f776fb3ce5-local-contract-v1", "task_id": TASK_ID,
            "generator_sha256": source_hash, "catalog_rule_hash": description["rule_hash"],
            "probe_sha256": sha(Path(__file__).read_bytes()),
            "canonical_records": canonical_records,
            "counts": {"binary": 512, "palette": len(probes) - 512, "total": len(probes),
                       "validator_accepted": accepted, "predicate_failures": len(failures)},
            "verdict": "FAIL" if failures else "PASS", "predicate_failures": failures,
            "generated_support": {"tested": False,
                "note": "3x3 corpus and 3x7 companions are outside documented generated dimensions 6..14. Validator acceptance and public rule applicability do not establish generated support."},
            "scope": "Exhaustive binary 3x3 only; compact palette extensions. No lesson or rotation claim. Rivals outside this local corpus may survive.",
            "rivals": scores, "authority_batches": receipts}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--binary-only", action="store_true")
    parser.add_argument("--timeout", type=float, default=120)
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error(f"Refusing to overwrite {args.out}")
    root = find_root(__file__)
    source = next(p for p in (root / "generators" / TASK_ID / "generator.py",
                             root / "puzzle_generators/per_puzzle" / TASK_ID / "generator.py") if p.is_file())
    spec = importlib.util.spec_from_file_location("local_contract_generator", source)
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    from arcpuzzles import Catalog
    catalog = Catalog(root if (root / "catalog/puzzles.jsonl").is_file() else None)
    invocation = {"argv": [sys.executable, str(Path(__file__).resolve()), *sys.argv[1:]],
                  "cwd": str(Path.cwd()), "exit_code": None}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as handle:
        try:
            report = build_report(generator, catalog, source, root,
                                  binary_only=args.binary_only, timeout=args.timeout)
            code = 1 if report["verdict"] == "FAIL" else 0
        except Exception as exc:
            report = {"schema": "80f776fb3ce5-local-contract-v1", "task_id": TASK_ID,
                      "verdict": "ERROR", "error": f"{type(exc).__name__}: {exc}",
                      "generator_sha256": sha(source.read_bytes())}
            if hasattr(exc, "run"):
                report["failure_receipt"] = exc.run
            code = 2
        report["invocation"] = {**invocation, "exit_code": code}
        json.dump(report, handle, indent=2); handle.write("\n")
    print(json.dumps({"out": str(args.out), "verdict": report["verdict"], "exit_code": code}))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
