"""Reproduce canonical-fitting shortcuts and source-bound generated witnesses.

Run through review.py run. First create the input manifest; label its inputs
with the public arcpuzzles apply command, then pass that receipt back using
--racket-report. No private runtime implementation or cached module aliases.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "15e7e0613c19"


def normalized(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def immutable_json(path, value):
    data = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if path.exists():
        if path.read_text() != data:
            raise ValueError(f"Refusing to overwrite different evidence: {path}")
    else:
        with path.open("x") as handle:
            handle.write(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket-report", type=Path)
    args = parser.parse_args()
    root = find_root(__file__)
    gen, source, digest = load_selected_generator(TASK_ID, root=root)
    canonical = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    rivals = gen.CANONICAL_SHORTCUTS
    if not rivals or not canonical:
        raise ValueError("Canonical labelled pairs and explicit rivals are required")
    fit = {}
    for name, rival in rivals.items():
        fit[name] = {"fits": sum(rival(p["input"]) == p["output"] for p in canonical),
                     "pairs": len(canonical)}
        if fit[name]["fits"] != len(canonical):
            raise ValueError(f"Declared shortcut {name} does not fit every canonical pair")
    witnesses = {}
    grids = []
    grid_indices = {}
    draws = 0
    for index in range(30):
        grid = gen.generate(0, index, difficulty="medium")
        draws += 1
        if gen.self_check(grid):
            raise ValueError("Generated witness outside domain")
        answer = gen.solve_reference(grid)
        for name, rival in rivals.items():
            if name not in witnesses and rival(grid) != answer:
                key = hashlib.sha256(normalized(grid)).hexdigest()
                if key not in grid_indices:
                    grid_indices[key] = len(grids)
                    grids.append(grid)
                witnesses[name] = {
                    "seed": 0, "sample_index": index, "difficulty": "medium", "overrides": {},
                    "input_index": grid_indices[key], "input": grid,
                    "mirror_output": answer, "rival_output": rival(grid),
                    "self_check": [], "input_sha256": key,
                    "objects": [{k: obj[k] for k in ("color", "area", "height", "width")}
                                for obj in gen._objects(grid)]}
        if len(witnesses) == len(rivals):
            break
    if set(witnesses) != set(rivals):
        raise ValueError("Bounded search did not find every declared witness")
    args.out.mkdir(parents=True, exist_ok=True)
    manifest = {"schema": "gallery-shortcut-probe-v1", "task_id": TASK_ID,
                "generator_sha256": digest, "generator_version": gen.VERSION,
                "declared_rule_hash": gen.RULE_HASH, "canonical_fit": fit,
                "draws_examined": draws, "unique_inputs": len(grids), "witnesses": witnesses}
    immutable_json(args.out / "inputs.json", {"inputs": grids})
    immutable_json(args.out / "manifest.json", manifest)
    if args.racket_report:
        receipt = json.loads(args.racket_report.read_text())
        if receipt.get("generator_sha256") != digest:
            raise ValueError("Authoritative receipt is bound to a different generator")
        if receipt.get("task_id") != TASK_ID or receipt.get("reference") != "canonical" or receipt.get("executed_rule_hash") != gen.RULE_HASH:
            raise ValueError("Unexpected task or Racket authority")
        results = receipt["results"]
        if len(results) != len(grids):
            raise ValueError("Racket input count differs")
        for grid, result in zip(grids, results):
            if result["input"] != grid or result.get("error") or result.get("valid_output") is not True:
                raise ValueError("Invalid or reordered authoritative result")
            if result["output"] != gen.solve_reference(grid):
                raise ValueError("Python mirror disagrees with canonical Racket")
        checks = {}
        for name, witness in witnesses.items():
            output = results[witness["input_index"]]["output"]
            if output == witness["rival_output"]:
                raise ValueError("Authoritative label does not separate the proposed rival")
            checks[name] = {"status": "racket_verified_difference", "output": output,
                            "seed": witness["seed"], "sample_index": witness["sample_index"]}
        verification = {"generator_sha256": digest, "racket_receipt_sha256": hashlib.sha256(args.racket_report.read_bytes()).hexdigest(),
                        "executed_rule_hash": receipt["executed_rule_hash"],
                        "rule_text_sha256": receipt["rule_text_sha256"],
                        "authoritative_inputs": len(results), "rivals_separated": len(checks), "checks": checks}
        immutable_json(args.out / "verification.json", verification)
    print(json.dumps({"generator_sha256": digest, "canonical_pairs": len(canonical),
                      "rivals": len(rivals), "draws": draws, "unique_inputs": len(grids),
                      "racket_verified": bool(args.racket_report)}, sort_keys=True))


if __name__ == "__main__":
    main()
