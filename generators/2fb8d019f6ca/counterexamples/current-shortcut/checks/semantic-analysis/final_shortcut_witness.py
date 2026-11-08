"""Bind a retained final-generated shortcut witness to independent public apply."""
from pathlib import Path
import hashlib
import json
import sys

from reviewer_support import canonical_pairs, load_selected_generator

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[1]
REPO = WORK / "repo"
TASK = "2fb8d019f6ca"
SOURCE = "95bd2548bd79c429eb3c5f27584de455463528a41c7697da90cf28dab26f1ad0"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def grid_sha(grid):
    return sha(json.dumps(grid, separators=(",", ":")).encode())


def prepare():
    census_path = WORK / "checks/lesson-final.json"
    census = json.loads(census_path.read_text())
    assert census["generator_sha256"] == SOURCE
    lesson = census["lessons"][8]
    accepted = next(row for row in lesson["instance"]["sampling"]["accepted_pairs"]
                    if row["split"] == "train" and row["pair_index"] == 1)
    assert accepted["sample_index"] == 9
    pair = lesson["instance"]["train"][1]
    gen, source, source_hash = load_selected_generator(TASK, root=REPO)
    assert source_hash == SOURCE
    reproduced = gen.generate(lesson["seed"], accepted["sample_index"], difficulty=lesson["band"])
    assert reproduced == pair["input"]
    assert grid_sha(reproduced) == accepted["input_sha256"]
    assert not gen.self_check(reproduced)
    canonical = canonical_pairs(TASK, root=REPO)
    fits = {name: sum(rival(p["input"]) == p["output"] for p in canonical)
            for name, rival in gen.CANONICAL_SHORTCUTS.items()}
    assert len(canonical) == 5 and set(fits.values()) == {5}
    selected = {
        "task_id": TASK, "generator_version": gen.VERSION,
        "generator_source_sha256": source_hash, "seed": lesson["seed"],
        "sample_index": accepted["sample_index"], "difficulty": lesson["band"], "overrides": {},
        "profile": gen.schedule_profile(lesson["seed"], accepted["sample_index"], lesson["band"]),
        "census_path": "checks/lesson-final.json", "census_sha256": sha(census_path.read_bytes()),
        "lesson_index": 8, "requested_start": lesson["sample_index"],
        "instance_sha256": lesson["instance_sha256"], "accepted_pair": accepted,
        "generation_reproduced_exactly": True, "input": reproduced,
        "census_output": pair["output"], "canonical_pairs": len(canonical),
        "canonical_rival_fits": fits,
        "rule_source_sha256": census["rule_source_sha256"],
        "rule_callable_sha256": census["rule_callable_sha256"],
        "declared_rule_hash": census["declared_rule_hash"],
    }
    (HERE / "final_generated_selection.json").write_text(json.dumps(selected, indent=2) + "\n")
    (HERE / "final_generated_input.json").write_text(json.dumps({"input": reproduced}, indent=2) + "\n")
    print(json.dumps({key: selected[key] for key in (
        "generator_source_sha256", "seed", "sample_index", "difficulty", "profile", "accepted_pair")}, indent=2))


def finalize():
    selected = json.loads((HERE / "final_generated_selection.json").read_text())
    applied_path = HERE / "final_generated_apply.json"
    applied = json.loads(applied_path.read_text())
    actual = applied["results"][0]
    assert applied["generator_sha256"] == selected["generator_source_sha256"] == SOURCE
    assert applied["rule_text_sha256"] == selected["rule_callable_sha256"]
    assert applied["executed_rule_hash"] == selected["declared_rule_hash"]
    assert actual["input"] == selected["input"]
    assert actual["valid_output"] and actual["error"] is None
    assert actual["output"] == selected["census_output"]
    assert actual["generator_domain"]["status"] == "valid"
    gen, source, source_hash = load_selected_generator(TASK, root=REPO)
    assert source_hash == SOURCE
    comparisons = {}
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        prediction = rival(actual["input"])
        changes = [{"row": r, "column": c, "reference": actual["output"][r][c], "rival": prediction[r][c]}
                   for r in range(len(prediction)) for c in range(len(prediction[0]))
                   if prediction[r][c] != actual["output"][r][c]]
        assert changes
        comparisons[name] = {"canonical_fit": f"{selected['canonical_rival_fits'][name]}/5",
                             "prediction_sha256": grid_sha(prediction), "differences": changes}
    primary = "all_non_anchor_pixels"
    assert comparisons[primary]["differences"] == [{"row": 4, "column": 4, "reference": 0, "rival": 3}]
    artifact = {
        "schema": "arcpuzzles-generated-shortcut-counterexample-v1", "task_id": TASK,
        "generator_version": selected["generator_version"], "generator_source_sha256": SOURCE,
        "generation": {key: selected[key] for key in ("seed", "sample_index", "difficulty", "overrides", "profile")},
        "emission_evidence": {key: selected[key] for key in (
            "census_path", "census_sha256", "lesson_index", "requested_start", "instance_sha256",
            "accepted_pair", "generation_reproduced_exactly")},
        "strongest_rival": primary,
        "rival_rule": "Copy every non-{0,8} input pixel at every 8 anchor, ignoring rooted 4-connectivity; retain blank canvas, input offsets, clipping and transparent row-major stamping.",
        "input": actual["input"], "input_sha256": actual["input_sha256"],
        "reference_output": actual["output"], "reference_output_sha256": actual["output_sha256"],
        "strongest_rival_output": gen.CANONICAL_SHORTCUTS[primary](actual["input"]),
        "rivals": comparisons,
        "reference_verification": {
            "method": "Independent public arcpuzzles apply with --reference canonical",
            "evidence_path": "checks/semantic-analysis/final_generated_apply.json",
            "evidence_sha256": sha(applied_path.read_bytes()), "command": applied["command"],
            "cwd": applied["cwd"], "exit_code": 0, "matches_census_label": True,
            "raw_rule_source_sha256": selected["rule_source_sha256"],
            "wrapped_callable_sha256": applied["rule_text_sha256"],
            "normalized_rule_id": applied["executed_rule_hash"],
        },
        "scope": "An actual ordinary odd draw from final v3.0.0, regenerated byte-for-byte. Period 2 governs default draws; overrides can remove the witness and accepted-index skips can alter lesson composition. Finite declared-rival evidence does not prove universal identifiability.",
    }
    output_path = REPO / f"generators/{TASK}/counterexamples/final-generated-shortcut.json"
    output_path.write_text(json.dumps(artifact, indent=2) + "\n")
    receipt = {"schema": "final-generated-shortcut-verification-v1", "task_id": TASK,
               "generator_source_sha256": SOURCE,
               "counterexample_path": str(output_path.relative_to(WORK)),
               "counterexample_sha256": sha(output_path.read_bytes()),
               "probe_source_sha256": sha(Path(__file__).read_bytes()),
               "cwd": str(WORK.parent),
               "commands": [
                   {"argv": ["python3", "review.py", "run", "python3", "../checks/semantic-analysis/final_shortcut_witness.py", "prepare"], "exit_code": 0},
                   {"argv": ["python3", "review.py", "run", "python3", "-m", "arcpuzzles", "apply", TASK, "--input", "../checks/semantic-analysis/final_generated_input.json", "--reference", "canonical", "--check-generator-domain", "--out", "../checks/semantic-analysis/final_generated_apply.json"], "exit_code": 0},
                   {"argv": ["python3", "review.py", "run", "python3", "../checks/semantic-analysis/final_shortcut_witness.py", "finalize"], "exit_code": 0}],
               "environment": {"PYTHONDONTWRITEBYTECODE": "1", "TMPDIR": "/dev/shm/arcpuzzles-review-ccdb-tmp"},
               "result": {"input_reproduced": True, "reference_matches_census": True,
                          "canonical_pairs_checked": 5, "canonical_rivals_fitting": 4,
                          "generated_input_refutes_each_rival": True}}
    (HERE / "final_generated_commands.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"counterexample": str(output_path), "source_sha256": SOURCE,
                      "input_sha256": actual["input_sha256"], "strongest_rival_changes": comparisons[primary]["differences"],
                      "rival_difference_counts": {name: len(row["differences"]) for name, row in comparisons.items()}}, indent=2))


if __name__ == "__main__":
    {"prepare": prepare, "finalize": finalize}[sys.argv[1]]()
