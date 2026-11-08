"""Replay small tail-transport counterexamples against the public Racket API.

From WORK: python3 run_with_racket.py python3   generators/0d1deab2505c/workspace/probe_transport.py --out ../checks/transport-probe
This is an authoring probe with reference labels, never a visible-only solve tool.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root

TASK_ID = "0d1deab2505c"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def fixture(height, width, creatures):
    # Expected outputs come from this explicit placement recipe, independently
    # of the generator parser, diagnostic transformer, and rival implementations.
    grid = [[8] * width for _ in range(height)]
    expected = [[8] * width for _ in range(height)]
    for center, arms, tail, shift in creatures:
        r, c = center
        dr, dc = shift
        cells = [(r, c, 4), (r-1, c, arms[0]), (r+1, c, arms[1]),
                 (r, c-1, arms[2]), (r, c+1, arms[3])]
        for rr, cc in tail:
            assert grid[rr][cc] == 8
            grid[rr][cc] = 1
            assert expected[rr+dr][cc+dc] == 8
            expected[rr+dr][cc+dc] = 1
        for rr, cc, value in cells:
            assert grid[rr][cc] == 8
            grid[rr][cc] = value
        turned = [(r, c, 4), (r-1, c, arms[1]), (r+1, c, arms[0]),
                  (r, c-1, arms[3]), (r, c+1, arms[2])]
        for rr, cc, value in turned:
            assert expected[rr+dr][cc+dc] == 8
            expected[rr+dr][cc+dc] = value
    return grid, expected


def make_cases():
    right = fixture(9, 11, [((4, 3), (2, 6, 3, 7),
                             [(4, 5), (4, 6), (4, 7)], (0, -2))])
    asymmetric = fixture(9, 12, [((4, 6), (9, 2, 5, 0),
                                  [(4, 4), (4, 3), (4, 2), (5, 2)], (0, 4))])
    mixed = fixture(12, 15, [
        ((3, 4), (2, 6, 3, 7), [(3, 6), (3, 7), (3, 8)], (0, -3)),
        ((8, 9), (0, 9, 5, 2), [(8, 7), (8, 6), (7, 5), (9, 5)], (0, 4)),
    ])
    movable = [0, 2, 3, 5, 6, 7, 9]
    permutation = dict(zip(movable, movable[1:] + movable[:1]))
    def permute(grid):
        return [[permutation.get(c, c) for c in row] for row in grid]
    return [
        ("straight_length3", *right),
        ("asymmetric_side_tip", *asymmetric),
        ("two_mixed_tails", *mixed),
        ("body_palette_permutation", permute(mixed[0]), permute(mixed[1])),
    ]


def declarations(module):
    for namespace in ("SEMANTIC_RIVALS", "CANONICAL_SHORTCUTS", "LESSON_COMPETITORS"):
        for name, function in getattr(module, namespace, {}).items():
            yield namespace + "." + name, function


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.out.exists():
        raise SystemExit("Choose a new output directory; prior evidence is preserved.")
    args.out.mkdir(parents=True)
    root = find_root(__file__)
    source = root / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location("transport_probe_generator", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    cases = make_cases()
    # Exact ordinary-generation replay, using public advertised controls.
    overrides = {"grid_h": 12, "grid_w": 15, "creature_count": 2,
                 "tail_direction": "right", "tail_length": 3,
                 "tail_branch": False, "palette_size": 10}
    generated = module.generate(seed=0, sample_index=1, difficulty="medium", **overrides)
    cases.append(("generated_exact_overrides", generated, None))
    inputs = [case[1] for case in cases]
    (args.out / "input.json").write_text(json.dumps(inputs, separators=(",", ":")) + "\n")
    reference = Catalog(root).apply(TASK_ID, inputs, timeout=120)
    reference["probe_command"] = ["python3", "run_with_racket.py", "python3",
        "generators/" + TASK_ID + "/workspace/probe_transport.py", "--out", str(args.out)]
    reference["probe_cwd"] = "packet_root"
    (args.out / "racket.json").write_text(json.dumps(reference, indent=2) + "\n")
    records = []
    errors = []
    reference_errors = []
    for (name, grid, expected), result in zip(cases, reference["results"], strict=True):
        output = result["output"]
        reference_error = result.get("error") if not result.get("valid_output", False) else None
        if reference_error or output is None:
            reference_errors.append(name + ": " + str(reference_error or "missing Racket output"))
        validation = module.self_check(grid)
        valid = not validation if isinstance(validation, list) else bool(validation)
        predictions = {}
        for rival_name, rival in declarations(module):
            try:
                prediction = rival(grid)
                predictions[rival_name] = {"output": prediction, "agrees": prediction == output}
            except Exception as exc:
                predictions[rival_name] = {"error": type(exc).__name__ + ": " + str(exc)}
                errors.append(name + " rival " + rival_name + " errored")
        if not valid:
            errors.append(name + " rejected by self_check: " + repr(validation))
        if output is not None and expected is not None and expected != output:
            errors.append(name + " differs from independently placed expected output")
        if output is not None and module.diagnostic_transform(grid) != output:
            errors.append(name + " diagnostic transformer differs from Racket")
        records.append({"name": name, "input": grid, "input_sha256": digest(grid),
            "actual_racket_output": output, "reference_error": reference_error, "independent_expected_output": expected,
            "self_check": validation, "valid": valid, "rivals": predictions,
            **({"replay": {"seed": 0, "sample_index": 1, "difficulty": "medium",
                            "overrides": overrides}} if expected is None else {})})
    canonical = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    fits = {}
    for name, rival in declarations(module):
        passed = 0
        for pair in canonical:
            try:
                passed += rival(pair["input"]) == pair["output"]
            except Exception as exc:
                errors.append("canonical rival " + name + " errored: " + str(exc))
        fits[name] = {"passed": passed, "total": len(canonical), "fits_all": passed == len(canonical)}
        if name.startswith("CANONICAL_SHORTCUTS.") and passed != len(canonical):
            errors.append(name + " does not fit all usable canonical pairs")
    report = {"schema": "0d1deab2505c-transport-probe-v1",
        "task_id": TASK_ID, "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "rule_text_sha256": reference["rule_text_sha256"],
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "declared_rivals": list(fits), "canonical_fit": fits, "cases": records,
        "status": "reference_error" if reference_errors else ("fail" if errors else "pass"), "errors": errors, "reference_errors": reference_errors,
        "limitations": "Five exact inputs, not a domain census. Fixed role colors 1,4,8 are never permuted."}
    (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "cases": len(records),
                      "generator_sha256": report["generator_sha256"], "errors": errors, "reference_errors": reference_errors}))
    raise SystemExit(2 if reference_errors else bool(errors))


if __name__ == "__main__":
    main()
