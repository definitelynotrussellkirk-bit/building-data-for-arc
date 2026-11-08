"""Source-bound dimension-template teaching audit; no target modifications.

Run prepare, apply the canonical Racket rule through the public CLI, then verify.
No private runtime runner functions are called.
"""
import sys
sys.dont_write_bytecode = True

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

TASK = "28b87bd4c441"
EXPECTED_SOURCE = "29036f7470aca505bde6c0a0f047c9a131ab22a9a27abcd6b111d333ea6ebc2e"
EXPECTED_CANONICAL_TEXT = "d488617f0f22d0115b860791a46ebdb0b32dd15c52cbbd12f0c2612c95addb7c"
EXPECTED_RULE_TEXT = "de53f267bd26799af3ea4e32aa312f48e2ecedd51ea7819b0861e167bc3921df"
RUNS = [(0, "easy"), (17, "medium"), (20261020, "hard")]
HERE = Path(__file__).resolve().parent


def write_json(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load_source(repo):
    source = repo / "generators" / TASK / "generator.py"
    data = source.read_bytes()
    assert digest(data) == EXPECTED_SOURCE, "Audited generator source changed"
    spec = importlib.util.spec_from_file_location("audit_generator_28b87bd4c441", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for line in (repo / "shared/data/canonical/puzzles.jsonl").open():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            break
    else:
        raise AssertionError("Canonical record missing")
    rule = row["program_solution"]
    assert digest(rule.encode()) == EXPECTED_CANONICAL_TEXT, "Audited canonical rule changed"
    return module, data, row


def integer_grid(grid):
    return [[int(cell) for cell in row] for row in grid]


def canonical_pairs(row):
    test = row["test"]
    tests = test if isinstance(test, list) else [test]
    return [{"input": integer_grid(pair["input"]), "output": integer_grid(pair["output"])}
            for pair in row["train"] + tests]


def marker(grid):
    points = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    assert len(points) == 1
    return points[0]


def learn_dimension_templates(demos):
    """Memorize each demo output's gray offsets, keyed only by grid dimensions."""
    templates = {}
    for pair in demos:
        grid, output = pair["input"], pair["output"]
        key = (len(grid), len(grid[0]))
        mr, mc = marker(grid)
        shape = tuple((r - mr, c - mc) for r, row in enumerate(output)
                      for c, value in enumerate(row) if value == 5)
        assert key not in templates or templates[key] == shape, "Shape varied within one grid size"
        templates[key] = shape
    return templates


def template_rival(grid, templates):
    """Ignore every gray cell in the query; stamp the size-selected template at red."""
    height, width = len(grid), len(grid[0])
    mr, mc = marker(grid)
    output = [[0] * width for _ in range(height)]
    for dr, dc in templates[(height, width)]:
        r, c = mr + dr, mc + dc
        assert 0 <= r < height and 0 <= c < width
        output[r][c] = 5
    return output


def prepare(repo):
    module, source, canonical = load_source(repo)
    pairs = canonical_pairs(canonical)
    assert len(pairs) == 4
    records = [{"index": i, "kind": "canonical_train" if i < 3 else "canonical_test"}
               for i in range(4)]
    inputs = [pair["input"] for pair in pairs]
    for seed, difficulty in RUNS:
        for sample_index in range(9):
            grid = module.generate(seed, sample_index, difficulty=difficulty)
            assert module.self_check(grid, difficulty=difficulty) == []
            records.append({"index": len(inputs), "kind": "generated", "seed": seed,
                            "difficulty": difficulty, "sample_index": sample_index,
                            "profile": module.observe_overrides(grid)["scene_profile"]})
            inputs.append(grid)
    assert len(inputs) == 31
    (HERE / "input.json").write_text(json.dumps({"inputs": inputs}, separators=(",", ":")) + "\n")
    (HERE / "source_snapshot.py").write_bytes(source)
    (HERE / "canonical_rule.rkt").write_text(canonical["program_solution"])
    write_json("canonical_record.json", canonical)
    write_json("input_index.json", records)
    bindings = {
        "task_id": TASK, "generator_version": module.VERSION,
        "generator_sha256": digest(source), "rule_text_sha256": EXPECTED_RULE_TEXT,
        "canonical_program_sha256": EXPECTED_CANONICAL_TEXT,
        "rule_hash": digest(" ".join(canonical["program_solution"].split()).encode())[:12],
        "generator_relative_path": f"repo/generators/{TASK}/generator.py",
        "canonical_relative_path": "repo/shared/data/canonical/puzzles.jsonl",
        "canonical_record_sha256": digest(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()),
        "runs": [{"seed": seed, "difficulty": difficulty, "sample_indices": list(range(9))}
                 for seed, difficulty in RUNS],
    }
    write_json("source_bindings.json", bindings)
    print(json.dumps({"prepared_inputs": len(inputs), "generated_inputs": 27, **bindings}))


def verify(repo):
    module, _, canonical = load_source(repo)
    assert digest((HERE / "source_snapshot.py").read_bytes()) == EXPECTED_SOURCE
    assert canonical == json.loads((HERE / "canonical_record.json").read_text())
    canonical_expected = canonical_pairs(canonical)
    application = json.loads((HERE / "racket.json").read_text())
    inputs = json.loads((HERE / "input.json").read_text())["inputs"]
    records = json.loads((HERE / "input_index.json").read_text())
    results = application["results"]
    assert len(results) == len(inputs) == 31
    assert application["generator_sha256"] == EXPECTED_SOURCE
    assert application["rule_text_sha256"] == EXPECTED_RULE_TEXT
    assert application["rule_hash_matches_catalog"]
    pairs = []
    for index, (grid, result) in enumerate(zip(inputs, results)):
        assert result["input"] == grid
        assert result["output"] is not None, result
        assert result["valid_output"] is True and result["error"] is None, result
        assert result["generator_domain"] == {"status": "valid", "errors": []}, result
        assert module.self_check(grid) == []
        assert result["output"] == module.rule_mirror(grid), index
        if index < 4:
            assert result["output"] == canonical_expected[index]["output"], index
        pairs.append({"input": grid, "output": result["output"]})

    query = pairs[3]
    assert module.self_check(query["input"]) == []
    assert module.strict_canonical_like(query["input"]) == []
    try:
        query_profile = module.observe_overrides(query["input"])
    except ValueError as exc:
        query_profile = {"outside_exact_generated_profile": str(exc)}

    checks = []
    for run_index, (seed, difficulty) in enumerate(RUNS):
        start = 4 + run_index * 9
        demos = pairs[start:start + 8]
        generated_query = pairs[start + 8]
        templates = learn_dimension_templates(demos)
        assert len(templates) == 8
        assert module.lesson_identifiable(demos, generated_query) == []
        assert module.lesson_identifiable(demos, query) == []
        assert all(template_rival(pair["input"], templates) == pair["output"] for pair in demos)
        assert template_rival(generated_query["input"], templates) == generated_query["output"]
        assert all(template_rival(pair["input"], templates) == pair["output"] for pair in pairs[:3])
        rival_output = template_rival(query["input"], templates)
        assert rival_output != query["output"]
        differences = [{"row": r, "column": c, "racket": query["output"][r][c], "rival": value}
                       for r, row in enumerate(rival_output) for c, value in enumerate(row)
                       if value != query["output"][r][c]]
        assert len(differences) == 2
        checks.append({"seed": seed, "difficulty": difficulty,
                       "generated_demo_indices": list(range(start, start + 8)),
                       "generated_query_index": start + 8,
                       "ordered_generated_lesson_hook": [], "canonical_query_lesson_hook": [],
                       "template_fit_generated_demos": 8, "template_fit_generated_query": True,
                       "template_fit_canonical_train": 3, "query_differences": differences})
        if run_index == 0:
            write_json("counterexample.json", {
                "task_id": TASK, "generator_sha256": EXPECTED_SOURCE,
                "rule_text_sha256": EXPECTED_RULE_TEXT,
                "demonstrations": demos, "query_input": query["input"],
                "racket_output": query["output"], "template_rival_output": rival_output,
                "differences": differences,
                "self_check": [], "strict_canonical_like": [], "lesson_identifiable": [],
                "query_profile_observation": query_profile,
                "dimension_templates": {f"{h}x{w}": shape for (h, w), shape in templates.items()},
                "query_provenance": "the unchanged canonical labeled test input",
            })
    summary = {
        "task_id": TASK, "generator_sha256": EXPECTED_SOURCE,
        "rule_text_sha256": EXPECTED_RULE_TEXT, "rule_hash": application["executed_rule_hash"],
        "canonical_program_sha256": EXPECTED_CANONICAL_TEXT,
        "finding": "dimension-conditioned fixed-shape teaching shortcut",
        "racket_inputs": 31, "generated_inputs": 27, "canonical_inputs": 4,
        "racket_vs_mirror_matches": 31, "canonical_label_matches": 4,
        "validator_accepts": 31, "observed_generated_profiles": sorted({r["profile"] for r in records if "profile" in r}),
        "template_matches_generated": 27, "template_matches_canonical_train": 3,
        "canonical_test_template_differences": 2,
        "canonical_query_self_check": [], "canonical_query_strict_canonical_like": [],
        "canonical_query_profile_observation": query_profile,
        "accepted_generated_lessons": 3, "accepted_canonical_query_lessons": 3,
        "checks": checks,
        "scope": "No wrong Racket labels or generated-profile output failures found. This is a shortcut/coverage finding on a validator-accepted canonical query outside the eight exact generated profiles.",
        "target_modified": False, "approval_changed": False,
    }
    write_json("audit_summary.json", summary)
    print(json.dumps(summary, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "verify"])
    parser.add_argument("--repo", type=Path, default=HERE.parents[2] / "repo")
    args = parser.parse_args()
    (prepare if args.action == "prepare" else verify)(args.repo.resolve())


if __name__ == "__main__":
    main()
