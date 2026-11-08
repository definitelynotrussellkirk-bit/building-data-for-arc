"""Source-bound override audit. Run from WORK/repo using the authoring Python.

prepare writes inputs; verify compares only to supported Racket apply results.
No source modifications, private answers, or solve artifacts are needed.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import itertools
import json

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs

TASK = "5d59b75cb58e"
HOME = Path(__file__).resolve().parent
ROOT = HOME.parents[2] / "repo"


def dump(name, value):
    (HOME / name).write_text(json.dumps(value, indent=2) + "\n")


def load_gen():
    source = ROOT / "generators" / TASK / "generator.py"
    spec = importlib.util.spec_from_file_location("audit_generator", source)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    return gen


def transpose_add(grid):
    output = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                output[c][r] = value
    return output


def prepare():
    gen = load_gen()
    description = Catalog(ROOT).get(TASK)
    rule = description["variants"][0]["program_solution"]
    files = [f"generators/{TASK}/generator.py",
             f"generators/{TASK}/notes.md", f"generators/{TASK}/SUMMARY.md",
             "shared/runtime/puzzle_generators/base.py"]
    dump("hashes.json", {
        "generator_sha256": description["generator_sha256"],
        "canonical_rule_hash": description["rule_hash"],
        "canonical_rule_sha256": hashlib.sha256(rule.encode()).hexdigest(),
        "canonical_rule_normalized_sha256": hashlib.sha256(" ".join(rule.split()).encode()).hexdigest(),
        "canonical_rule": rule,
        "files": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files},
    })
    records = []
    grids = []

    def append(kind, grid, **details):
        records.append({"index": len(grids), "kind": kind,
                        "self_check_errors": gen.self_check(grid),
                        "documented_grid_domain": not gen.self_check(grid), **details})
        grids.append(grid)

    # Exactly documented joint boundary controls, with no source-side coercion.
    for side, n_blobs, blob_size, source_sides in itertools.product(
            (8, 12), (2, 3), (3, 5), ("lower", "upper", "both")):
        axes = dict(side=side, n_blobs=n_blobs, blob_size=blob_size, source_sides=source_sides)
        grid = gen.generate(29051, 7, difficulty="hard", **axes)
        observed = gen.observe_overrides(grid)
        assert observed == axes
        append("legal_boundary_override", grid, seed=29051, sample_index=7,
               difficulty="hard", overrides=axes, observed=observed,
               documented_override_domain=True)

    # Each three-slot unforced lesson should teach both source directions.
    for band in ("easy", "medium", "hard"):
        for index in range(3):
            grid = gen.generate(29051, index, difficulty=band)
            append("default_schedule", grid, seed=29051, sample_index=index,
                   difficulty=band, overrides={}, observed=gen.observe_overrides(grid),
                   documented_override_domain=True)

    for pair in canonical_pairs(TASK, root=ROOT):
        append("canonical", pair["input"], variant=pair["variant"],
               split=pair["split"], pair_index=pair["pair_index"],
               canonical_output=pair["output"])

    # These requests exceed the advertised upper bounds and are not integers.
    # The generator silently truncates each and produces a validator-passing grid.
    for name, value in (("side", 12.75), ("n_blobs", 3.75), ("blob_size", 5.75)):
        axes = dict(side=8, n_blobs=2, blob_size=3, source_sides="upper")
        axes[name] = value
        grid = gen.generate(29051, 1, difficulty="medium", **axes)
        observed = gen.observe_overrides(grid)
        assert observed[name] == int(value) and observed[name] != value
        assert not gen.self_check(grid)
        append("accepted_invalid_override", grid, seed=29051, sample_index=1,
               difficulty="medium", overrides=axes, observed=observed,
               documented_override_domain=False, offending_axis=name,
               supplied_value=value, actual_value=observed[name])

    assert len(grids) <= 64
    dump("input.json", grids)
    dump("cases.json", records)
    print(json.dumps({"prepared_inputs": len(grids),
                      "invalid_override_requests_accepted": 3,
                      "all_inputs_pass_self_check": all(not row["self_check_errors"] for row in records)}))


def verify():
    gen = load_gen()
    grids = json.loads((HOME / "input.json").read_text())
    records = json.loads((HOME / "cases.json").read_text())
    authority = json.loads((HOME / "racket.json").read_text())
    # The record shape is supported by the public apply command.
    print(json.dumps({"authority_keys": list(authority)}))
    outputs = [result["output"] for result in sorted(authority["results"], key=lambda result: result["index"])]
    assert authority["executed_rule_hash"] == "2b970065d6a3"
    assert authority["generator_sha256"] == json.loads((HOME / "hashes.json").read_text())["generator_sha256"]
    assert len(outputs) == len(grids)
    mismatches = [i for i, (grid, output) in enumerate(zip(grids, outputs))
                  if transpose_add(grid) != output]
    assert not mismatches
    for row in records:
        if row["kind"] == "canonical":
            assert outputs[row["index"]] == row["canonical_output"]
    lessons = []
    for band in ("easy", "medium", "hard"):
        rows = [r for r in records if r["kind"] == "default_schedule" and r["difficulty"] == band]
        assert {r["observed"]["source_sides"] for r in rows} == {"lower", "upper", "both"}
        # Hold out each of these three materialized pairs once.
        pairs = [{"input": grids[r["index"]], "output": outputs[r["index"]]} for r in rows]
        for held_out in range(3):
            errors = gen.lesson_identifiable([p for i, p in enumerate(pairs) if i != held_out], pairs[held_out])
            assert not errors
            lessons.append({"difficulty": band, "held_out_index": held_out,
                            "declared_rivals_surviving_with_query_disagreement": errors})
    summary = {"status": "finding", "finding": "fractional out-of-range exact integer overrides silently truncated",
               "racket_inputs_checked": len(grids), "transpose_label_mismatches": mismatches,
               "valid_joint_boundary_controls_checked": 24,
               "invalid_override_requests_accepted": [r for r in records if r["kind"] == "accepted_invalid_override"],
               "bounded_teaching_checks": lessons,
               "limits": "One seed; 24 joint boundary controls; nine default inputs; three canonical pairs; three malformed overrides. Declared rivals only; no universal induction claim."}
    dump("summary.json", summary)
    print(json.dumps({"racket_inputs_checked": len(grids), "transpose_label_mismatches": mismatches,
                      "fractional_overrides_accepted": 3, "declared_rival_rotations_checked": len(lessons)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("prepare", "verify"))
    phase = parser.parse_args().phase
    prepare() if phase == "prepare" else verify()
