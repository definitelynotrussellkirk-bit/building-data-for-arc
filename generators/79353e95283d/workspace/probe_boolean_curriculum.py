#!/usr/bin/env python3
"""Probe aligned Boolean evidence for 79353e95283d without running Racket.

Run from any directory in either a library or a copied runtime. Generated
comparisons use a local Python AND table, not authoritative reference execution.
Only the smallest seed witnessing each reported feature/table outcome is kept.

Example: python probe_boolean_curriculum.py --seeds 600 --out report.json
The separate --self-test mode checks table indexing against literal expected
outputs; its synthetic truth grid is never included in a sampling report.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import types


TASK_ID = "79353e95283d"
STATES = ("00", "01", "10", "11")
TABLE_NAMES = (
    "zero", "nor", "right_only", "not_left", "left_only", "not_right",
    "xor", "nand", "and", "equal", "right", "left_implies_right",
    "left", "right_implies_left", "or", "two",
)


def support_imports():
    """Bootstrap only from this file's own tree, then use the public helper."""
    for parent in Path(__file__).resolve().parents:
        for directory in (parent / "shared/runtime", parent):
            if (directory / "reviewer_support.py").is_file():
                sys.path.insert(0, str(directory))
                from reviewer_support import canonical_pairs, canonical_path, find_root
                return find_root(__file__), canonical_pairs, canonical_path
    raise FileNotFoundError("reviewer_support.py not found in this file's tree")


def digest_bytes(value):
    return hashlib.sha256(value).hexdigest()


def digest_json(value):
    return digest_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def state_rows(grid):
    if not isinstance(grid, list) or not grid:
        raise ValueError("Expected a nonempty panel grid")
    result = []
    for row in grid:
        if not isinstance(row, list) or len(row) != 7:
            raise ValueError("Expected width 7")
        if any(type(value) is not int or not 0 <= value <= 9 for value in row):
            raise ValueError("Expected integer colors 0..9")
        if any(row[c] not in (0, 1) for c in (0, 1, 2, 4, 5, 6)):
            raise ValueError("Expected binary panels")
        result.append([2 * row[c] + row[c + 4] for c in range(3)])
    return result


def boolean_output(grid, mask):
    """Bit i supplies the output for state i=2*left+right, in 00,01,10,11 order."""
    if type(mask) is not int or not 0 <= mask < 16:
        raise ValueError("Boolean mask must be an integer in 0..15")
    return [[2 * ((mask >> state) & 1) for state in row] for row in state_rows(grid)]


def self_test():
    truth_grid = [[0, 0, 1, 5, 0, 1, 0], [1, 0, 1, 5, 1, 0, 1]]
    assert state_rows(truth_grid) == [[0, 1, 2], [3, 0, 3]]
    assert boolean_output(truth_grid, 8) == [[0, 0, 0], [2, 0, 2]]
    assert boolean_output(truth_grid, 12) == [[0, 0, 2], [2, 0, 2]]
    assert boolean_output(truth_grid, 10) == [[0, 2, 0], [2, 0, 2]]
    assert boolean_output(truth_grid, 6) == [[0, 2, 2], [0, 0, 0]]
    outputs = set()
    for mask in range(16):
        a, b, c, d = [2 * int(bool(mask & bit)) for bit in (1, 2, 4, 8)]
        expected = [[a, b, c], [d, a, d]]
        actual = boolean_output(truth_grid, mask)
        assert actual == expected, (mask, actual, expected)
        outputs.add(json.dumps(actual))
    assert len(outputs) == 16
    for invalid in (-1, 16, True, 8.0):
        try:
            boolean_output(truth_grid, invalid)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Accepted invalid Boolean mask {invalid!r}")
    return {"self_test": "pass", "tables_checked": 16, "state_order": STATES}


def probe(args):
    root, canonical_pairs, canonical_path = support_imports()
    candidates = (root / "generators" / TASK_ID / "generator.py",
                  root / "puzzle_generators/per_puzzle" / TASK_ID / "generator.py")
    source_path = next((path for path in candidates if path.is_file()), None)
    if source_path is None:
        raise FileNotFoundError(f"Generator {TASK_ID} not found under {root}")
    source = source_path.read_bytes()
    module = types.ModuleType(f"boolean_probe_{TASK_ID}")
    module.__file__ = str(source_path)
    sys.modules[module.__name__] = module
    exec(compile(source, str(source_path), "exec"), module.__dict__)
    pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    if not pairs:
        raise ValueError("No labeled canonical pairs")

    tables = []
    for mask, name in enumerate(TABLE_NAMES):
        fit = [boolean_output(pair["input"], mask) == pair["output"] for pair in pairs]
        tables.append({
            "mask": mask, "name": name,
            "output_by_state": {state: 2 * ((mask >> i) & 1) for i, state in enumerate(STATES)},
            "canonical_pairs_fit": sum(fit), "fits_all_canonical_pairs": all(fit),
            "generated_matches_python_and": 0, "generated_differs_from_python_and": 0,
            "first_match_seed": None, "first_difference_seed": None,
        })

    counts = Counter(attempted=args.seeds)
    cell_counts = Counter({state: 0 for state in STATES})
    grids_with_state = Counter({state: 0 for state in STATES})
    profiles, heights, separators = Counter(), Counter(), Counter()
    first, witnesses, errors = {}, {}, {}

    def remember(feature, seed, grid=None, states=None):
        if feature in first:
            return
        first[feature] = seed
        if grid is not None and str(seed) not in witnesses:
            witnesses[str(seed)] = {
                "seed": seed, "sample_index": args.sample_index,
                "difficulty": args.difficulty, "input": grid,
                "input_sha256": digest_json(grid), "truth_state_counts": dict(states),
            }

    for seed in range(args.seed_start, args.seed_start + args.seeds):
        try:
            grid = module.generate(seed, args.sample_index, difficulty=args.difficulty)
        except Exception as exc:
            counts["generation_errors"] += 1
            errors.setdefault("generation", {"seed": seed, "error": f"{type(exc).__name__}: {exc}"})
            continue
        counts["generated"] += 1
        try:
            indexed = state_rows(grid)
            states = Counter({state: 0 for state in STATES})
            states.update(STATES[state] for row in indexed for state in row)
            python_and = boolean_output(grid, 8)
        except Exception as exc:
            counts["analysis_errors"] += 1
            errors.setdefault("analysis", {"seed": seed, "error": f"{type(exc).__name__}: {exc}"})
            continue
        counts["analyzed"] += 1
        cell_counts.update(states)
        grids_with_state.update(state for state in STATES if states[state])
        profiles["|".join(state for state in STATES if states[state])] += 1
        heights[str(len(grid))] += 1
        separators[",".join(map(str, sorted({row[3] for row in grid})))] += 1
        features = {
            "all_four_states": all(states.values()),
            "same_panels": not states["01"] and not states["10"],
            "copy_left_matches_and": not states["10"],
            "copy_right_matches_and": not states["01"],
            "either_copy_matches_and": not states["10"] or not states["01"],
            "canonical_geometry_palette": len(grid) == 3 and all(row[3] == 5 for row in grid),
        }
        features["canonical_geometry_palette_with_all_states"] = (
            features["canonical_geometry_palette"] and features["all_four_states"])
        features.update({f"missing_{state}": not states[state] for state in STATES})
        for feature, holds in features.items():
            counts[feature] += int(holds)
            if holds:
                remember(feature, seed, grid, states)
        for mask, table in enumerate(tables):
            matches = boolean_output(grid, mask) == python_and
            key = "match" if matches else "difference"
            table["generated_matches_python_and" if matches else "generated_differs_from_python_and"] += 1
            if table[f"first_{key}_seed"] is None:
                table[f"first_{key}_seed"] = seed
                remember(f"table_{mask}_{key}", seed, grid, states)
        if hasattr(module, "self_check"):
            try:
                reasons = module.self_check(grid, difficulty=args.difficulty)
                if reasons:
                    counts["self_check_rejections"] += 1
                    errors.setdefault("self_check", {"seed": seed, "reasons": reasons})
            except Exception as exc:
                counts["self_check_exceptions"] += 1
                errors.setdefault("self_check_exception", {"seed": seed, "error": f"{type(exc).__name__}: {exc}"})

    ledger = canonical_path(root)
    return {
        "schema": "arcpuzzles-boolean-curriculum-probe-v1", "task_id": TASK_ID,
        "generator_version": getattr(module, "VERSION", None),
        "generator_path": str(source_path.relative_to(root)),
        "generator_sha256": digest_bytes(source),
        "probe_sha256": digest_bytes(Path(__file__).read_bytes()),
        "argv": sys.argv, "arguments": vars(args), "state_order": STATES,
        "evidence_basis": {
            "generated": "Local Python Boolean-table comparison; no Racket was executed.",
            "canonical": "Existing labeled canonical ledger pairs; not freshly executed reference labels.",
        },
        "canonical": {
            "ledger_path": str(ledger.relative_to(root)),
            "ledger_sha256": digest_bytes(ledger.read_bytes()),
            "normalized_pairs_sha256": digest_json(pairs), "pair_count": len(pairs),
            "pair_identities": [{key: pair[key] for key in ("variant", "split", "pair_index")} for pair in pairs],
        },
        "counts": dict(counts), "truth_state_cell_counts": dict(cell_counts),
        "grids_with_truth_state": dict(grids_with_state),
        "truth_state_profiles": dict(sorted(profiles.items())),
        "height_counts": dict(sorted(heights.items(), key=lambda row: int(row[0]))),
        "separator_counts": dict(sorted(separators.items())),
        "boolean_tables": tables, "first_seed_by_feature": first,
        "first_errors": errors, "witnesses": witnesses,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--seeds", type=int, default=600)
    parser.add_argument("--sample-index", type=int, default=0)
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"))
    parser.add_argument("--out", help="New JSON report path; stdout if omitted")
    parser.add_argument("--self-test", action="store_true", help="Run only embedded table-indexing checks")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), sort_keys=True))
        return 0
    if args.seeds < 1 or args.sample_index < 0:
        parser.error("--seeds must be positive and --sample-index nonnegative")
    report = probe(args)
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        with Path(args.out).open("x", encoding="utf-8") as handle:
            handle.write(encoded)
        print(json.dumps({"out": args.out, "generator_sha256": report["generator_sha256"],
                          "counts": report["counts"], "witness_grids": len(report["witnesses"])}, sort_keys=True))
    else:
        print(encoded, end="")
    return int(bool(report["first_errors"]))


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    raise SystemExit(main())
