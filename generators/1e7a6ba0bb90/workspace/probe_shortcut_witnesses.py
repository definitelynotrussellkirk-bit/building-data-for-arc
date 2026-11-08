"""Build and verify source-bound shortcut witnesses using public Racket labels.

From the review packet's outer root (choose a fresh --out directory):
  python3 review.py run python3 generators/1e7a6ba0bb90/workspace/probe_shortcut_witnesses.py build --out ../checks/final-witnesses-v2
  python3 review.py run python3 -m arcpuzzles apply 1e7a6ba0bb90 --input ../checks/final-witnesses-v2/input.json --out ../checks/final-witnesses-v2/racket.json
  python3 review.py run python3 generators/1e7a6ba0bb90/workspace/probe_shortcut_witnesses.py verify --out ../checks/final-witnesses-v2

This authoring probe reads actual generator declarations. It never supplies
Python predictions as authoritative labels or changes generator/rule files.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
TASK = "1e7a6ba0bb90"
SOURCE = Path(__file__).resolve().parents[1] / "generator.py"

# The same public helper is available at runtime root or shared/runtime in a
# library. Locate it only through this file's ancestors, never through cwd or
# a sibling checkout.
try:
    from reviewer_support import canonical_pairs, canonical_path, find_root
except ModuleNotFoundError:
    for ancestor in Path(__file__).resolve().parents:
        support = ancestor / "shared/runtime"
        if (support / "reviewer_support.py").is_file():
            sys.path.insert(0, str(support))
            break
    from reviewer_support import canonical_pairs, canonical_path, find_root

ROOT = find_root(__file__)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_generator(expected=None):
    source_hash = sha(SOURCE.read_bytes())
    if expected and source_hash != expected:
        raise AssertionError(f"source binding changed: expected {expected}, got {source_hash}")
    spec = importlib.util.spec_from_file_location(f"witness_target_{TASK}", SOURCE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module, source_hash


def build(out, expected):
    module, source_hash = load_generator(expected)
    declarations = {name: getattr(module, name) for name in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS")}
    assert all(isinstance(rows, dict) and rows and all(isinstance(name, str) and callable(fn) for name, fn in rows.items())
               for rows in declarations.values())
    pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    assert len(pairs) == 4, f"expected this task's four usable canonical pairs, got {len(pairs)}"
    programs = set()
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK:
                    programs.add(row["program_solution"])
    assert len(programs) == 1, "ambiguous canonical rule identity"
    inputs, by_hash = [], {}

    def add(grid, origin):
        digest = sha(encoded(grid))
        if digest not in by_hash:
            problems = module.self_check(grid)
            assert problems == [], (origin, problems)
            answer = module.predict_for_authoring(grid)
            record = {"input_id": f"input_{len(inputs):02d}", "input_sha256": digest, "input": grid,
                      "origins": [], "self_check": problems, "authoring_output": answer,
                      "observed_axes": module.observe_overrides(grid),
                      "rival_outputs": {ns: {name: fn(grid) for name, fn in funcs.items()}
                                        for ns, funcs in declarations.items()}}
            by_hash[digest] = record
            inputs.append(record)
        record = by_hash[digest]
        record["origins"].append(origin)
        return record

    canonical_ids = []
    for pair in pairs:
        origin = {"kind": "canonical", "variant": pair["variant"], "split": pair["split"],
                  "pair_index": pair["pair_index"], "canonical_output": pair["output"]}
        record = add(pair["input"], origin)
        assert record["authoring_output"] == pair["output"]
        canonical_ids.append(record["input_id"])

    generated_ids = []
    for index in range(9):
        call = {"seed": 0, "sample_index": index, "difficulty": "medium", "overrides": {}}
        record = add(module.generate(0, index, difficulty="medium"), {"kind": "generated_schedule", "generate_call": call})
        generated_ids.append(record["input_id"])

    literal_path = SOURCE.parent / "counterexamples/clockwise_vs_counterclockwise.json"
    literal = json.loads(literal_path.read_text(encoding="utf-8"))
    literal_record = add(literal["input"], {"kind": "literal_counterexample", "source_path": str(literal_path.relative_to(ROOT)),
        "file_sha256_at_build": sha(literal_path.read_bytes()), "recorded_generator_sha256": literal.get("generator_sha256"),
        "recorded_rule_hash": literal.get("rule_hash"), "recorded_racket_output": literal["racket_output"],
        "rival_name": literal["rival_name"], "recorded_rival_output": literal["rival_output"]})
    assert literal_record["authoring_output"] == literal["racket_output"]
    assert literal_record["rival_outputs"]["CANONICAL_SHORTCUTS"][literal["rival_name"]] == literal["rival_output"]
    assert literal["racket_output"] != literal["rival_output"]

    regression_call = {"seed": 92, "sample_index": 2, "difficulty": "hard", "overrides": {}}
    regression = add(module.generate(92, 2, difficulty="hard"), {"kind": "vertical_alignment_regression", "generate_call": regression_call})
    assert regression["rival_outputs"]["CANONICAL_SHORTCUTS"]["retain_relative_vertical_offset"] != regression["authoring_output"]
    lookup = {row["input_id"]: row for row in inputs}
    canonical_fit, witnesses = {}, {}
    for namespace, funcs in declarations.items():
        canonical_fit[namespace], witnesses[namespace] = {}, {}
        for name in funcs:
            canonical_fit[namespace][name] = all(lookup[rid]["rival_outputs"][namespace][name] == lookup[rid]["authoring_output"] for rid in canonical_ids)
            available = [rid for rid in generated_ids if lookup[rid]["rival_outputs"][namespace][name] != lookup[rid]["authoring_output"]]
            assert available, f"no actual no-override generated witness for {namespace}:{name}"
            witnesses[namespace][name] = {"chosen_input_id": available[0], "all_schedule_witness_ids": available}
    assert all(canonical_fit["CANONICAL_SHORTCUTS"].values()), "a declared canonical shortcut is not canonical-fitting"

    witness_claims = []
    for record in inputs:
        for name, predicate in getattr(module, "SEMANTIC_WITNESSES", {}).items():
            fired = predicate(record["input"])
            assert type(fired) is bool, f"non-boolean semantic witness {name}"
            if not fired:
                continue
            names = module.WITNESS_RIVALS[name]
            names = [names] if isinstance(names, str) else list(names)
            predictions = {rn: module.SEMANTIC_RIVALS[rn](record["input"]) for rn in names}
            assert any(value != record["authoring_output"] for value in predictions.values())
            witness_claims.append({"input_id": record["input_id"], "witness_name": name, "linked_rival_outputs": predictions})
    report = {"schema": "shortcut-witness-probe-v1", "task_id": TASK,
              "generator_sha256": source_hash, "generator_version": module.VERSION, "declared_rule_hash": module.RULE_HASH,
              "canonical_program_sha256": sha(next(iter(programs)).encode()),
              "canonical_pairs_checked": len(pairs), "canonical_input_ids": canonical_ids,
              "generated_schedule_input_ids": generated_ids, "literal_input_id": literal_record["input_id"],
              "vertical_alignment_input_id": regression["input_id"],
              "declarations": {ns: sorted(funcs) for ns, funcs in declarations.items()},
              "canonical_fit": canonical_fit, "generated_witnesses": witnesses,
              "semantic_witness_claims": witness_claims, "inputs": inputs,
              "build_invocation": {"argv": sys.argv, "cwd": str(Path.cwd())}}
    out.mkdir(parents=True, exist_ok=True)
    assert not (out / "witnesses.json").exists(), "choose a new output directory"
    write_json(out / "input.json", {"inputs": [row["input"] for row in inputs]})
    write_json(out / "witnesses.json", report)
    print(json.dumps({"generator_sha256": source_hash, "unique_inputs": len(inputs),
                      "canonical_pairs": len(pairs), "declaration_counts": {ns: len(rows) for ns, rows in declarations.items()},
                      "generated_witnesses_complete": True, "out": str(out)}, indent=2))


def verify(out, expected):
    report = json.loads((out / "witnesses.json").read_text(encoding="utf-8"))
    module, source_hash = load_generator(expected or report["generator_sha256"])
    assert source_hash == report["generator_sha256"]
    authority = json.loads((out / "racket.json").read_text(encoding="utf-8"))
    assert authority["generator_sha256"] == source_hash
    assert authority["executed_rule_hash"] == report["declared_rule_hash"] == module.RULE_HASH
    assert authority["rule_hash_matches_catalog"] is True
    rows = report["inputs"]
    assert json.loads((out / "input.json").read_text(encoding="utf-8")) == {"inputs": [row["input"] for row in rows]}
    assert len(rows) == len(authority["results"])
    lookup, outputs = {row["input_id"]: row for row in rows}, {}
    for record, actual in zip(rows, authority["results"]):
        grid, answer = record["input"], actual["output"]
        assert actual["input"] == grid and actual["valid_output"] is True and actual["error"] is None
        assert sha(encoded(grid)) == record["input_sha256"]
        assert answer == record["authoring_output"] == module.predict_for_authoring(grid), record["input_id"]
        outputs[record["input_id"]] = answer
        for origin in record["origins"]:
            if "canonical_output" in origin:
                assert answer == origin["canonical_output"]
            if "recorded_racket_output" in origin:
                assert answer == origin["recorded_racket_output"]
        for namespace, names in report["declarations"].items():
            assert names == sorted(getattr(module, namespace)), f"changed declarations: {namespace}"
            for name in names:
                assert getattr(module, namespace)[name](grid) == record["rival_outputs"][namespace][name]
    for namespace, items in report["generated_witnesses"].items():
        for name, claim in items.items():
            for rid in claim["all_schedule_witness_ids"]:
                assert lookup[rid]["rival_outputs"][namespace][name] != outputs[rid], (namespace, name, rid)
            assert claim["chosen_input_id"] in claim["all_schedule_witness_ids"]
            fit = all(lookup[rid]["rival_outputs"][namespace][name] == outputs[rid] for rid in report["canonical_input_ids"])
            assert fit == report["canonical_fit"][namespace][name]
            if namespace == "CANONICAL_SHORTCUTS":
                assert fit
    for claim in report["semantic_witness_claims"]:
        assert any(value != outputs[claim["input_id"]] for value in claim["linked_rival_outputs"].values()), claim
    regression_id, literal_id = report["vertical_alignment_input_id"], report["literal_input_id"]
    assert outputs[regression_id] != lookup[regression_id]["rival_outputs"]["CANONICAL_SHORTCUTS"]["retain_relative_vertical_offset"]
    assert outputs[literal_id] != lookup[literal_id]["rival_outputs"]["CANONICAL_SHORTCUTS"]["key_1_means_ccw"]
    result = {"schema": "shortcut-witness-verification-v1", "task_id": TASK, "generator_sha256": source_hash,
              "executed_rule_hash": authority["executed_rule_hash"], "rule_text_sha256": authority["rule_text_sha256"],
              "canonical_program_sha256": report["canonical_program_sha256"],
              "authoritative_input_count": len(rows), "canonical_pairs_checked": report["canonical_pairs_checked"],
              "canonical_shortcuts_fitting_all_pairs": len(report["declarations"]["CANONICAL_SHORTCUTS"]),
              "declaration_counts_with_generated_witnesses": {ns: len(items) for ns, items in report["generated_witnesses"].items()},
              "semantic_witness_claims_verified": len(report["semantic_witness_claims"]),
              "all_racket_outputs_match_authoring": True, "all_claimed_rival_differences_verified": True,
              "literal_counterexample_verified": True, "seed_92_index_2_hard_vertical_alignment_verified": True,
              "source_witnesses_sha256": sha((out / "witnesses.json").read_bytes()),
              "source_racket_sha256": sha((out / "racket.json").read_bytes()),
              "source_input_sha256": sha((out / "input.json").read_bytes()),
              "probe_sha256": sha(Path(__file__).read_bytes()),
              "verify_invocation": {"argv": sys.argv, "cwd": str(Path.cwd())}}
    write_json(out / "verification.json", result)
    lines = ["# Final-source shortcut witness verification", "",
             f"Generator SHA-256: `{source_hash}`. Rule hash: `{result['executed_rule_hash']}`.", "",
             f"All {len(rows)} canonical Racket outputs match the generator's authoring predictions. "
             f"All {result['canonical_shortcuts_fitting_all_pairs']} declared canonical shortcuts fit all four usable canonical labels, "
             "and each has a differing actual no-override generated witness.", "",
             "The seed-0 medium samples at indices 0 through 8 provide witnesses for every actual declaration in "
             "CANONICAL_SHORTCUTS and LESSON_COMPETITORS. The retained literal CW/CCW input and final-source "
             "seed-92/index-2/hard vertical-alignment case were independently labelled in the same Racket batch.", "",
             "| Canonical shortcut | First generated witness | All schedule witness indices |",
             "|---|---|---|"]
    for name, claim in report["generated_witnesses"]["CANONICAL_SHORTCUTS"].items():
        indices = []
        for rid in claim["all_schedule_witness_ids"]:
            indices.extend(origin["generate_call"]["sample_index"] for origin in lookup[rid]["origins"] if origin["kind"] == "generated_schedule")
        chosen = lookup[claim["chosen_input_id"]]
        origin = next(origin for origin in chosen["origins"] if origin["kind"] == "generated_schedule")
        lines.append(f"| `{name}` | seed 0, index {origin['generate_call']['sample_index']}, medium | {', '.join(map(str, indices))} |")
    lines += ["", "This is source-bound finite evidence against the declared rivals. Intermediate evidence directories "
              "were not changed. The literal input's pre-existing metadata binding is recorded in witnesses.json; "
              "the present verification is bound to the final generator hash above.", "",
              "Full inputs, authoring predictions, rival predictions, source origins and semantic-witness claims: witnesses.json. "
              "Authoritative labels: racket.json. Verification receipt: verification.json.", ""]
    (out / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("build", "verify"))
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--expect-generator-sha256")
    args = parser.parse_args()
    {"build": build, "verify": verify}[args.action](args.out.resolve(), args.expect_generator_sha256)
