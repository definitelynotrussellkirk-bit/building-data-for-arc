"""Small read-only, actual-Racket audit of the pinned hole-count generator.

Run through review.py run. Writes only beside this script; does not patch the
audited generator, rule, catalog, or shared runtime. Exit 0 means evidence was
completed, not that no audit finding exists.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator


TASK_ID = "9e80ef661ecc"
EXPECTED_SOURCE = "b60ba4b5640da51fde70f6ba8c114942f31c7535ac12b70c55fc68d2cd4fc51d"


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def paint(grid, rows, origin, color):
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            if value == "1":
                assert grid[origin[0] + r][origin[1] + c] == 0
                grid[origin[0] + r][origin[1] + c] = color


def nested_scene(fill):
    grid = [[0] * 15 for _ in range(11)]
    paint(grid, ["111111", "100001", "100001", "100001", "100001", "111111"], (1, 1), 1)
    paint(grid, fill, (2, 2), 5)
    paint(grid, ["11111", "10101", "11111"], (1, 9), 8)
    return grid


def main():
    out = Path(__file__).resolve().parent
    root = find_root(__file__)
    module, source, source_sha = load_selected_generator(TASK_ID, root=root)
    assert source_sha == EXPECTED_SOURCE, (source_sha, EXPECTED_SOURCE)
    row = next(json.loads(line) for line in canonical_path(root).read_text().splitlines()
               if json.loads(line).get("task_id") == TASK_ID)
    rule = row["program_solution"]
    rule_hash = hashlib.sha256(" ".join(rule.split()).encode()).hexdigest()[:12]
    assert rule_hash == module.RULE_HASH == "609d24e8c088"
    records = []
    for pair in canonical_pairs(TASK_ID, root=root):
        records.append({"kind": "canonical", "split": pair["split"],
                        "pair_index": pair["pair_index"], "input": pair["input"],
                        "canonical_output": pair["output"]})
    by_index = {}
    for index in sorted(set(range(12)) | {16, 24, 32}):
        grid = module.generate(0, index, difficulty="easy")
        by_index[index] = len(records)
        records.append({"kind": "generated", "seed": 0, "sample_index": index,
                        "difficulty": "easy", "overrides": {}, "input": grid,
                        "observed_profile": module.observe_overrides(grid)})
    for name, fill in (
        ("hole_filled_by_other_color", ["1111"] * 4),
        ("nested_ring", ["1111", "1001", "1001", "1111"]),
        ("inner_solid_with_background_gap", ["1100", "1100", "0000", "0000"]),
    ):
        records.append({"kind": "handmade", "name": name, "input": nested_scene(fill)})

    inputs = [record["input"] for record in records]
    before = digest(inputs)
    reference = Catalog(root).apply(TASK_ID, inputs, reference="canonical", check_generator_domain=True)
    assert reference["generator_sha256"] == source_sha
    assert reference["executed_rule_hash"] == rule_hash
    assert reference["rule_hash_matches_catalog"]
    assert digest(inputs) == before
    write(out / "reference.json", reference)
    parity_errors = []
    grammar_errors = []
    for i, (record, result) in enumerate(zip(records, reference["results"], strict=True)):
        assert result["valid_output"] and result["error"] is None, result
        record["output"] = result["output"]
        record["input_sha256"] = result["input_sha256"]
        record["output_sha256"] = result["output_sha256"]
        record["self_check"] = module.self_check(record["input"])
        record["strict_canonical_like"] = module.strict_canonical_like(record["input"])
        record["python_mirror_matches_racket"] = module.rule_mirror(record["input"]) == record["output"]
        if not record["python_mirror_matches_racket"]:
            parity_errors.append(i)
        if record["self_check"] or record["strict_canonical_like"]:
            grammar_errors.append(i)
        if "canonical_output" in record:
            assert record["canonical_output"] == record["output"]

    rivals = dict(module.LESSON_COMPETITORS)
    predictions = {name: [rival(record["input"]) for record in records] for name, rival in rivals.items()}

    def score(indices, position):
        q = indices[position]
        demos = [index for p, index in enumerate(indices) if p != position]
        fits = [name for name in rivals if all(predictions[name][i] == records[i]["output"] for i in demos)]
        ambiguous = [name for name in fits if predictions[name][q] != records[q]["output"]]
        equivalent = [name for name in fits if predictions[name][q] == records[q]["output"]]
        reasons = module.lesson_identifiable([records[i] for i in demos], records[q])
        return {"records": indices, "query_position": position, "query_record": q,
                "demo_records": demos, "ambiguous_rivals": ambiguous,
                "equivalent_survivors": equivalent, "hook_reasons": reasons,
                "hook_rejects_without_declared_query_ambiguity": bool(reasons) and not ambiguous}

    rotations = []
    for start in range(8):
        indices = [by_index[i] for i in range(start, start + 5)]
        for position in range(5):
            result = score(indices, position)
            result.update({"seed": 0, "difficulty": "easy", "start": start,
                           "sample_indices": list(range(start, start + 5)),
                           "production_query": position == 4})
            rotations.append(result)
    subset_indices = [by_index[i] for i in [0, 8, 16, 24, 32]]
    subset = score(subset_indices, 4)
    subset["sample_indices"] = [0, 8, 16, 24, 32]
    subset["policy"] = "diagnostic subset of ordinary draws; not a consecutive production lesson"
    subset["distinct_inputs"] = len({records[i]["input_sha256"] for i in subset_indices})

    first_ambiguity = next((result for result in rotations if result["ambiguous_rivals"]), None)
    witnesses = {}
    for name, result in (("rotation_ambiguity", first_ambiguity), ("equivalent_survivor_hook", subset)):
        if result is None:
            continue
        witnesses[name] = {"recipe": result,
                           "demos": [records[i] for i in result["demo_records"]],
                           "query": records[result["query_record"]],
                           "rival_outputs": {r: predictions[r][result["query_record"]]
                                             for r in result["ambiguous_rivals"] + result["equivalent_survivors"]}}
    summary = {
        "records": len(records), "canonical_pairs": 4, "generated_inputs": len(by_index),
        "handmade_nested_scenes": 3, "parity_errors": parity_errors, "grammar_errors": grammar_errors,
        "ordinary_production_lessons": 8,
        "production_ambiguities": sum(bool(r["ambiguous_rivals"]) for r in rotations if r["production_query"]),
        "production_hook_rejections": sum(bool(r["hook_reasons"]) for r in rotations if r["production_query"]),
        "query_rotations": len(rotations),
        "ambiguous_rotations": sum(bool(r["ambiguous_rivals"]) for r in rotations),
        "rotation_hook_false_positives": sum(r["hook_rejects_without_declared_query_ambiguity"] for r in rotations),
        "subset_hook_rejects_without_declared_query_ambiguity": subset["hook_rejects_without_declared_query_ambiguity"],
    }
    binding = {"task_id": TASK_ID, "generator_sha256": source_sha,
               "generator_path": source.relative_to(root).as_posix(), "rule_hash": rule_hash,
               "rule_text_sha256": hashlib.sha256(rule.encode()).hexdigest(),
               "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    write(out / "witnesses.json", {"source": binding, **witnesses})
    write(out / "probe.json", {"schema": "arcpuzzles-readonly-peer-audit-v1", "source": binding,
                               "execution": {"argv": [sys.executable, *sys.argv], "cwd": str(Path.cwd()),
                                             "source_root": str(root)},
                               "summary": summary, "rival_names": list(rivals), "records": records,
                               "rotations": rotations, "subset_diagnostic": subset})
    assert hashlib.sha256(source.read_bytes()).hexdigest() == source_sha
    print(json.dumps({"source": binding, "summary": summary, "first_rotation": first_ambiguity,
                      "subset_diagnostic": subset}, indent=2))


if __name__ == "__main__":
    main()
