"""Analysis-only rival witnesses for 2e663d812b7a; no generation dependency.

The local model is a transparent translation for probing. Racket remains the
label authority; this script compares its model to every stored canonical pair.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import itertools
import json
from pathlib import Path
import sys
import types

TASK = "2e663d812b7a"
HERE = Path(__file__).resolve()

# Bootstrap only the helper belonging to this script's own ancestor tree.
# reviewer_support.find_root then selects the library or portable runtime root.
for _ancestor in HERE.parents:
    _support_locations = (_ancestor, _ancestor / "shared" / "runtime")
    _support_parent = next((candidate for candidate in _support_locations
                            if (candidate / "reviewer_support.py").is_file()), None)
    if _support_parent is not None:
        sys.path.insert(0, str(_support_parent))
        break
else:
    raise FileNotFoundError("No local reviewer_support.py beside an ancestor runtime or library")
from reviewer_support import canonical_pairs, find_root  # noqa: E402

ROOT = find_root(HERE)


def selected_generator_path():
    for relative in (Path("generators") / TASK / "generator.py",
                     Path("puzzle_generators") / "per_puzzle" / TASK / "generator.py"):
        candidate = ROOT / relative
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("No selected generator source for " + TASK + " under " + str(ROOT))


def model(grid, mode="canonical"):
    h, w = len(grid), len(grid[0])
    key_len = max((c + 1 for c, color in enumerate(grid[0]) if color), default=0)
    key = grid[0][:key_len]
    sr, sc = next((r, c) for r in range(2, h) for c in range(w) if grid[r][c])
    radius = min(sr - 2, h - 1 - sr, sc, w - 1 - sc)
    if mode == "top_is_row_zero":
        radius = min(sr, h - 1 - sr, sc, w - 1 - sc)
    elif mode == "bottom_only":
        radius = h - 1 - sr
    out = [list(row) for row in grid]
    if mode != "keep_key":
        for c in range(radius + 1, key_len):
            if mode == "last_only" and c != key_len - 1:
                continue
            if grid[0][c] or mode == "gray_active_zeros":
                out[0][c] = 5
    body_key = key
    if mode == "compress_zeros":
        body_key = [color for color in key if color]
    elif mode == "deduplicate_adjacent":
        body_key = [color for i, color in enumerate(key) if i == 0 or color != key[i - 1]]
    elif mode == "paint_marked_key":
        body_key = out[0][:key_len]
    for r in range(2, h):
        for c in range(w):
            distance = max(abs(r - sr), abs(c - sc))
            if mode == "manhattan":
                distance = abs(r - sr) + abs(c - sc)
            if distance < len(body_key) and (mode != "complete_only" or distance <= radius):
                out[r][c] = body_key[distance]
    return out


def witness(h=16, w=16, key=(2, 3, 3, 0, 4, 6), seed=(3, 8)):
    grid = [[0] * w for _ in range(h)]
    grid[0][:len(key)] = key
    grid[1] = [5] * w
    grid[seed[0]][seed[1]] = key[0]
    return grid


def difference(expected, actual):
    changed = [(r, c, expected[r][c], actual[r][c])
               for r in range(len(expected)) for c in range(len(expected[0]))
               if expected[r][c] != actual[r][c]]
    return {"different_cells": len(changed), "first_differences": changed[:8]}


def load_contract(path):
    path = path.resolve()
    module = types.ModuleType("semantic_review_contract_" + TASK)
    module.__file__ = str(path)
    sys.modules[module.__name__] = module
    exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), vars(module))
    return module


def inspect_contract(contract, pairs, grid, expected):
    declarations = contract.SEMANTIC_RIVALS
    fits = {name: sum(rival(copy.deepcopy(p["input"])) == p["output"] for p in pairs)
            for name, rival in declarations.items()}
    shortcut_fits = {
        name: sum(rival(copy.deepcopy(pair["input"])) == pair["output"] for pair in pairs)
        for name, rival in contract.CANONICAL_SHORTCUTS.items()
    }
    refuted = {name: rival(copy.deepcopy(grid)) != expected
               for name, rival in declarations.items()}
    witness_hits = {name: bool(predicate(copy.deepcopy(grid)))
                    for name, predicate in contract.SEMANTIC_WITNESSES.items()}
    canonical_rejected = [i for i, pair in enumerate(pairs)
                          if contract.strict_canonical_like(pair["input"])]
    actual_model_matches = sum(contract._semantic_model(p["input"]) == p["output"] for p in pairs)
    model_witness_matches = contract._semantic_model(grid) == expected
    ordinary_demos = pairs[:2]
    rich_query = {"input": grid, "output": expected}
    ambiguous_reasons = contract.lesson_identifiable(ordinary_demos, rich_query)
    equivalent_reasons = contract.lesson_identifiable(ordinary_demos, pairs[2])
    rich_demo_reasons = contract.lesson_identifiable([rich_query], pairs[2])

    def injected_rival(input_grid):
        output_grid = model(input_grid)
        if input_grid == grid:
            output_grid[0][0] = (output_grid[0][0] + 1) % 10
        return output_grid

    dynamic_results = {}
    for declaration in ("LESSON_COMPETITORS", "CANONICAL_SHORTCUTS"):
        original = getattr(contract, declaration)
        replacement = dict(original)
        replacement["dynamic_probe"] = injected_rival
        setattr(contract, declaration, replacement)
        try:
            reasons = contract.lesson_identifiable(ordinary_demos, rich_query)
            dynamic_results[declaration] = any("dynamic_probe" in reason for reason in reasons)
        finally:
            setattr(contract, declaration, original)

    invalid_cases = {}
    no_separator = copy.deepcopy(grid)
    no_separator[1] = [0] * len(grid[0])
    invalid_cases["missing_separator"] = no_separator
    no_seed = copy.deepcopy(grid)
    no_seed[3][8] = 0
    invalid_cases["missing_seed"] = no_seed
    extra_seed = copy.deepcopy(grid)
    extra_seed[4][8] = 2
    invalid_cases["extra_seed"] = extra_seed
    mismatch = copy.deepcopy(grid)
    mismatch[3][8] = 1
    invalid_cases["seed_color_mismatch"] = mismatch
    invalid_results = {name: list(contract.strict_canonical_like(bad))
                       for name, bad in invalid_cases.items()}
    expected_shortcuts = set(contract.CANONICAL_SHORTCUTS)
    problems = []
    if canonical_rejected:
        problems.append("strict contract rejects canonical inputs")
    if actual_model_matches != len(pairs) or not model_witness_matches:
        problems.append("contract audit model disagrees with stored answers or independent witness model")
    if not all(refuted.values()) or not all(witness_hits.values()):
        problems.append("rich witness does not refute every declared rival or fire every distinguishing witness")
    if not expected_shortcuts:
        problems.append("no canonical shortcut declarations are available")
    if any(shortcut_fits[name] != len(pairs) for name in expected_shortcuts):
        problems.append("a declared canonical shortcut fails a canonical pair")
    if any(not any(name in reason for reason in ambiguous_reasons) for name in expected_shortcuts):
        problems.append("lesson hook misses a canonical-fitting, query-changing rival")
    if equivalent_reasons or rich_demo_reasons:
        problems.append("lesson hook rejects an answer-equivalent or rich-witness lesson")
    if not all(dynamic_results.values()):
        problems.append("lesson hook does not read both named declarations dynamically")
    if not all(invalid_results.values()):
        problems.append("strict contract accepts a malformed task-domain mutation")
    return {
        "canonical_model_matches": actual_model_matches,
        "canonical_rejected": canonical_rejected,
        "canonical_rival_matches": fits,
        "canonical_shortcut_matches": shortcut_fits,
        "rich_witness_model_matches": model_witness_matches,
        "rich_witness_refutes": refuted,
        "rich_witness_fires": witness_hits,
        "canonical_to_rich_query_ambiguity_reasons": ambiguous_reasons,
        "answer_equivalent_survivor_reasons": equivalent_reasons,
        "rich_demo_reasons": rich_demo_reasons,
        "dynamic_declaration_injection_detected": dynamic_results,
        "invalid_domain_reasons": invalid_results,
        "problems": problems,
    }


def inspect_rich_key_family(contract):
    """Enumerate four-color rich keys at canonical dimensions, modulo relabeling."""
    checked = 0
    failures = []
    for key_len in (6, 7, 8):
        for repeated in (1, 2):
            for zero_index in range(3, key_len - 1):
                positions = [i for i in range(3, key_len) if i != zero_index]
                for values in itertools.product((1, 2, 3, 4), repeat=len(positions)):
                    key = [1, repeated, repeated] + [0] * (key_len - 3)
                    for index, color in zip(positions, values):
                        key[index] = color
                    if len(set(key) - {0}) != 4:
                        continue
                    grid = witness(key=key)
                    expected = model(grid)
                    missed = [name for name, rival in contract.SEMANTIC_RIVALS.items()
                              if rival(grid) == expected]
                    checked += 1
                    if missed:
                        failures.append({"key": key, "unrefuted_rivals": missed})
    return {"h": 16, "w": 16, "seed": [3, 8], "keys_checked": checked,
            "keys_with_unrefuted_rivals": len(failures), "failure_examples": failures[:5]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path,
                        default=selected_generator_path(),
                        help="Final selected generator.py to load dynamically (a design snippet must be explicit)")
    parser.add_argument("--out", type=Path,
                        default=Path(__file__).with_name("semantic_review_probe.json"))
    parser.add_argument("--exhaustive-rich", action="store_true",
                        help="Enumerate 756 rich key patterns at 16x16, seed (3,8)")
    args = parser.parse_args(argv)
    pairs = canonical_pairs(TASK, root=ROOT)
    grid = witness()
    expected = model(grid)
    contract = load_contract(args.contract)
    comparisons = {}
    for name, rival in contract.SEMANTIC_RIVALS.items():
        predicted = rival(grid)
        comparisons[name] = {
            "canonical_matches": sum(rival(p["input"]) == p["output"] for p in pairs),
            "canonical_pairs": len(pairs),
            "witness_output_key": predicted[0][:6],
            **difference(expected, predicted),
        }
    inspected = inspect_contract(contract, pairs, grid, expected)
    if args.exhaustive_rich:
        rich_family = inspect_rich_key_family(contract)
        inspected["rich_key_family"] = rich_family
        if rich_family["keys_with_unrefuted_rivals"]:
            inspected["problems"].append("rich key family contains a non-distinguishing case")
    data = {
        "task_id": TASK,
        "status": "pass" if not inspected["problems"] else "fail",
        "contract_path": str(args.contract.resolve()),
        "contract_sha256": hashlib.sha256(args.contract.read_bytes()).hexdigest(),
        "analysis_model_canonical_matches": sum(model(p["input"]) == p["output"] for p in pairs),
        "canonical_pairs": len(pairs),
        "unique_canonical_pairs": len({json.dumps([p["input"], p["output"]]) for p in pairs}),
        "generator_sha256_when_run": hashlib.sha256(selected_generator_path().read_bytes()).hexdigest(),
        "witness": {"input": grid, "expected_model_output": expected,
                    "h": 16, "w": 16, "key": [2, 3, 3, 0, 4, 6], "seed": [3, 8],
                    "complete_radius": 1, "expected_output_key": expected[0][:6]},
        "rivals": comparisons,
        "contract_checks": inspected,
        "limitation": "Analysis model agrees with stored canonical answers; custom witness has not been executed through Racket by this probe.",
    }
    target = args.out.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": data["status"], "canonical_pairs": len(pairs),
                      "unique_canonical_pairs": data["unique_canonical_pairs"],
                      "contract_checks": inspected}, indent=2))
    print(target)
    return 1 if inspected["problems"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
