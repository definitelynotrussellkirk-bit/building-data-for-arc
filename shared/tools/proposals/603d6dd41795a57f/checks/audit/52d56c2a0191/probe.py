"""Source-bound, findings-only probe for the red selector curriculum."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator


TASK = "52d56c2a0191"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA = load_selected_generator(TASK, root=ROOT)


def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def component_sizes(grid, color):
    """Independent four-neighbor flood fill, with no generator helper calls."""
    remaining = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}
    sizes = []
    while remaining:
        start = remaining.pop()
        stack = [start]
        size = 0
        while stack:
            r, c = stack.pop()
            size += 1
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
        sizes.append(size)
    return sorted(sizes)


def rival(grid):
    counts = Counter(value for row in grid for value in row if value != 0)
    selected = min(counts, key=lambda color: (-counts[color], color))
    return selected, [component_sizes(grid, selected)]


def observe(grid):
    color, rival_output = rival(grid)
    expected = [component_sizes(grid, 2)]
    counts = Counter(value for row in grid for value in row if value != 0)
    return {
        "input_sha256": digest(grid),
        "shape": [len(grid), len(grid[0])],
        "foreground_counts": dict(sorted(counts.items())),
        "expected_output": expected,
        "mirror_output": GEN.rule_mirror(grid),
        "self_check": GEN.self_check(grid),
        "strict_canonical_like": GEN.strict_canonical_like(grid),
        "observed_overrides": GEN.observe_overrides(grid),
        "rival_selected_color": color,
        "rival_output": rival_output,
        "rival_matches": rival_output == expected,
        "red_dominance_margin": counts[2] - max((count for color, count in counts.items() if color != 2), default=0),
    }


def main():
    rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines() if line.strip()]
    rows = [row for row in rows if row.get("task_id") == TASK]
    rules = list(dict.fromkeys(row["program_solution"] for row in rows))
    identity = {
        "task_id": TASK,
        "generator_path": str(SOURCE.relative_to(ROOT)),
        "generator_sha256": SOURCE_SHA,
        "generator_version": GEN.VERSION,
        "declared_rule_hash": GEN.RULE_HASH,
        "canonical_rule": rules,
        "canonical_rule_text_sha256": [hashlib.sha256(rule.encode()).hexdigest() for rule in rules],
        "canonical_rule_normalized_hash": [hashlib.sha256(" ".join(rule.split()).encode()).hexdigest()[:12] for rule in rules],
        "task_file_sha256": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted((ROOT / "generators" / TASK).rglob("*"))
            if path.is_file() and "__pycache__" not in path.parts
        },
    }
    save("identity.json", identity)

    canonical_results = []
    oracle_inputs, oracle_cases = [], []

    def add_oracle_case(label, grid, request=None):
        record = observe(grid)
        record.update({"label": label, "input_index": len(oracle_inputs), "request": request})
        oracle_cases.append(record)
        oracle_inputs.append(grid)

    for pair in canonical_pairs(TASK, root=ROOT):
        label = f"canonical-v{pair['variant']}-{pair['split']}-{pair['pair_index']}"
        result = observe(pair["input"])
        result.update({"label": label, "canonical_output": pair["output"]})
        canonical_results.append(result)
        assert result["expected_output"] == pair["output"], label
        add_oracle_case(label, pair["input"])

    sampled = []
    for band in ("easy", "medium", "hard"):
        for profile in GEN.SCENE_PROFILES:
            for canvas in GEN.CANVAS_PROFILES:
                for seed in (0, 123, 20261020):
                    request = {"seed": seed, "sample_index": 9, "difficulty": band,
                               "overrides": {"scene_profile": profile, "canvas_profile": canvas}}
                    grid = GEN.generate(seed, 9, difficulty=band, **request["overrides"])
                    result = observe(grid)
                    result["request"] = request
                    assert result["observed_overrides"] == request["overrides"]
                    sampled.append(result)
                    if band == "medium" and seed == 20261020:
                        add_oracle_case(f"forced-{profile}-{canvas}", grid, request)
        for index in range(40):
            seed = 20261020 + index
            grid = GEN.generate(seed, index, difficulty=band)
            result = observe(grid)
            result["request"] = {"seed": seed, "sample_index": index, "difficulty": band, "overrides": {}}
            sampled.append(result)

    failures = [result for result in canonical_results + sampled
                if result["self_check"] or result["strict_canonical_like"]
                or result["mirror_output"] != result["expected_output"]]
    save("sample_failures.json", failures)
    assert not failures, failures

    # Build a compact accepted-domain discriminator from an exact generated input.
    # Red keeps its three components of sizes 1,2,3. An existing distractor color
    # is extended by seven cells, making it more frequent than red without
    # changing canvas dimensions, palette cardinality, or any red adjacency.
    base = None
    for seed in range(128):
        candidate = GEN.generate(seed, 0, difficulty="easy", scene_profile="canonical", canvas_profile="h10_w12_p7")
        if component_sizes(candidate, 2) == [1, 2, 3]:
            base = candidate
            request = {"seed": seed, "sample_index": 0, "difficulty": "easy",
                       "overrides": {"scene_profile": "canonical", "canvas_profile": "h10_w12_p7"}}
            break
    assert base is not None, "bounded search did not find the small canonical size tuple"
    color = min({value for row in base for value in row} - {0, 2})
    cells = None
    for r, row in enumerate(base):
        for c in range(len(row) - 6):
            if all(row[column] == 0 for column in range(c, c + 7)):
                cells = [(r, column) for column in range(c, c + 7)]
                break
        if cells:
            break
    assert cells is not None
    counterexample = deepcopy(base)
    for r, c in cells:
        counterexample[r][c] = color
    finding = {
        "task_id": TASK, "generator_sha256": SOURCE_SHA, "rule_hash": GEN.RULE_HASH,
        "kind": "unrefuted_color_selection_shortcut",
        "rival": "Choose the most frequent nonzero color, then return its sorted 4-connected component sizes; ties select the lowest color.",
        "base_request": request,
        "base_input": base,
        "mutation": {"operation": "replace seven zero cells with one existing non-red color", "color": color, "cells": cells},
        "input": counterexample,
        "observation": observe(counterexample),
        "origin": "authored mutation of an exact generated input, accepted by current validators; the sampler does not emit this dense-distractor pattern",
    }
    assert not finding["observation"]["self_check"]
    assert not finding["observation"]["strict_canonical_like"]
    assert not finding["observation"]["rival_matches"]
    save("counterexample.json", finding)
    save("input.json", counterexample)
    add_oracle_case("counterexample-base", base, request)
    add_oracle_case("counterexample-dominant-distractor", counterexample, request)
    save("apply_inputs.json", {"inputs": oracle_inputs})
    save("oracle_cases.json", oracle_cases)

    old_finding_path = ROOT / "generators" / TASK / "counterexamples/review-d956010e627d79d5-v0001/retained/checks/audit/52d56c2a0191/finding.json"
    old_finding = json.loads(old_finding_path.read_text())
    try:
        GEN.generate(123, 0, texture="no_red")
    except Exception as error:
        old_reproducer = {"raised": type(error).__name__, "message": str(error)}
    else:
        old_reproducer = {"raised": None}
    inherited_recheck = {
        "historical_source_sha256": old_finding["generator_sha256"],
        "current_source_sha256": SOURCE_SHA,
        "generate_123_0_texture_no_red": old_reproducer,
        "historical_input_current_self_check": GEN.self_check(old_finding["input"]),
        "audit_status_unchanged": "needs_triage",
    }
    save("inherited_recheck.json", inherited_recheck)

    summary = {
        "task_id": TASK, "generator_sha256": SOURCE_SHA, "rule_hash": GEN.RULE_HASH,
        "canonical_pairs": len(canonical_results),
        "canonical_rival_matches": sum(result["rival_matches"] for result in canonical_results),
        "sampled_grids": len(sampled),
        "forced_sample_lattice": {"seeds": [0, 123, 20261020], "sample_index": 9, "difficulties": ["easy", "medium", "hard"], "scene_profiles": list(GEN.SCENE_PROFILES), "canvas_profiles": list(GEN.CANVAS_PROFILES)},
        "default_sample_lattice": {"sample_indices": [0, 39], "seed": "20261020 + sample_index", "difficulties": ["easy", "medium", "hard"]},
        "generated_rival_matches": sum(result["rival_matches"] for result in sampled),
        "generated_rival_selected_colors": sorted({result["rival_selected_color"] for result in sampled}),
        "minimum_sampled_red_dominance_margin": min(result["red_dominance_margin"] for result in sampled),
        "sample_validation_or_mirror_failures": len(failures),
        "racket_inputs_prepared": len(oracle_inputs),
        "canonical_results": canonical_results,
        "counterexample_observation": finding["observation"],
        "inherited_recheck": inherited_recheck,
        "racket_status": "not yet executed",
    }
    save("probe_summary.json", summary)
    print(json.dumps({key: value for key, value in summary.items() if key not in ("canonical_results",)}, indent=2))


if __name__ == "__main__":
    main()
