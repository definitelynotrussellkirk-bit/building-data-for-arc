"""Synthetic generated envelopes with complete real canonical grids.

Actual Racket execution observations are retained separately in checks/.
"""
from copy import deepcopy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest
from reviewer_support import canonical_path, find_root

SCRIPT = Path(__file__).resolve().parents[1] / "workspace" / "check_output_profile_support.py"
spec = importlib.util.spec_from_file_location("output_profile_tool", SCRIPT)
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)
AUTHORITY = tool.canonical_authority(canonical_path(root=find_root(__file__)))


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def pair(visible):
    grid = [[0]*4 for _ in range(4)]
    for r,c in ((1,1),(1,2),(2,1)): grid[r][c] = 3
    out = [[0]*4 for _ in range(4)]
    for r,c in ((1,1),(1,2),(2,1))[:visible]: out[r][c] = 8
    return {"input": grid, "output": out}


def receipt(canonical=False, modes=(3,1,0)):
    pairs = deepcopy(list(AUTHORITY["pairs"].values())) if canonical else [pair(n) for n in modes]
    results = [{"index": i, **p, "valid_output": True, "error": None,
                "input_sha256": digest(p["input"]), "output_sha256": digest(p["output"])}
               for i,p in enumerate(pairs)]
    value = {"schema": "task-output-profile-observations-v1", "task_id": "8738d400fb96",
             "role": "canonical" if canonical else "generated", "adapter": tool.ADAPTER,
             "generator_sha256": "a"*64, "rule_callable_sha256": "b"*64,
             "executed_rule_hash": "fc4e32aa0363", "expected_pairs": len(pairs),
             "expected_apply_results": len(pairs), "bands": ["easy"] if not canonical else [],
             "samples": [{"result_index": i, **({"band": "easy"} if not canonical else {})}
                         for i in range(len(pairs))],
             "execution": {"exit_code": 0, "timed_out": False},
             "apply_receipt": {"schema": "arcpuzzles-apply-v1", "task_id": "8738d400fb96",
                               "reference": "canonical", "rule_text_sha256": "b"*64,
                               "executed_rule_hash": "fc4e32aa0363", "generator_sha256": "c"*64,
                               "rule_hash_matches_catalog": True, "results": results},
             "label_generator_sha256": "c"*64}
    if canonical:
        value.update(ledger_sha256=AUTHORITY["ledger_sha256"], canonical_program_sha256=AUTHORITY["program_sha256"])
        value["samples"] = [{"result_index": i, "split": split, "pair_index": index}
                            for i, (split, index) in enumerate(AUTHORITY["pairs"])]
    else:
        value["expected_per_band"] = {"easy": len(pairs)}
        value["generation"] = {"source_sha256": "a"*64, "expected_pairs": len(pairs),
                               "inputs_sha256": digest([p["input"] for p in pairs])}
    return value


def test_missing_partial_and_empty_profiles_are_detected_per_band():
    report = tool.analyze(receipt(canonical=True), receipt(modes=(3,3)))
    assert report["status"] == "missing_canonical_output_profiles"
    assert report["per_band"]["easy"]["missing"] == ["empty", "partial"]


def test_observed_all_profiles_is_finite_support():
    assert tool.analyze(receipt(canonical=True), receipt())["status"] == "observed_support_in_each_band"


def test_mass_uses_largest_cardinal_green_object_and_rejects_wrong_output_color():
    p = pair(3)
    p["input"][3][3] = 3  # diagonal contact does not join the main component
    assert tool.classify(p["input"], p["output"]) == "full"
    p["output"][0][0] = 7
    with pytest.raises(ValueError): tool.classify(p["input"], p["output"])


@pytest.mark.parametrize("damage", ["rule", "missing_result", "input_hash", "source", "incomplete",
                                    "adapter", "empty_band", "missing_sample", "wrong_output_shape"])
def test_invalid_or_unbound_observations_fail(damage):
    generated = receipt()
    if damage == "rule": generated["rule_callable_sha256"] = "f"*64
    elif damage == "missing_result": generated["apply_receipt"]["results"].pop()
    elif damage == "input_hash": generated["apply_receipt"]["results"][0]["input_sha256"] = "0"*64
    elif damage == "source": generated["generation"]["source_sha256"] = "f"*64
    elif damage == "incomplete": generated["execution"]["exit_code"] = 2
    elif damage == "adapter": generated["adapter"] = {"kind": "guessed"}
    elif damage == "empty_band": generated["bands"].append("hard")
    elif damage == "missing_sample": generated["samples"].pop()
    else: generated["apply_receipt"]["results"][0]["output"] = [[0]]
    with pytest.raises(ValueError): tool.analyze(receipt(canonical=True), generated)


def test_comparison_core_is_independent_of_task_adapter():
    result = tool.compare_support(["full", "partial"], {"easy": ["full"], "hard": ["partial"]})
    assert result["easy"]["missing"] == ["partial"]
    assert result["hard"]["missing"] == ["full"]


def test_cli_supports_gzip_and_exit1(tmp_path):
    a,b,out = tmp_path/"canonical.json.gz", tmp_path/"generated.json", tmp_path/"out.json"
    with gzip.open(a,"wt") as f: json.dump(receipt(canonical=True),f)
    b.write_text(json.dumps(receipt(modes=(3,))))
    run = subprocess.run([sys.executable,str(SCRIPT),"--canonical",str(a),"--generated",str(b),"--out",str(out)],capture_output=True,text=True)
    assert run.returncode == 1,run.stderr
    assert json.loads(out.read_text())["status"] == "missing_canonical_output_profiles"


def test_cli_incomplete_receipt_exit2(tmp_path):
    a,out = tmp_path/"bad.json",tmp_path/"out.json"
    a.write_text("{}")
    run = subprocess.run([sys.executable,str(SCRIPT),"--canonical",str(a),"--generated",str(a),"--out",str(out)],capture_output=True)
    assert run.returncode == 2
    assert json.loads(out.read_text())["status"] == "error"


@pytest.mark.parametrize("destination", ["canonical", "generated", "ledger", "existing", "symlink"])
def test_cli_preserves_existing_inputs_and_outputs(tmp_path, destination):
    canonical = tmp_path / "canonical.json"
    generated = tmp_path / "generated.json"
    ledger = tmp_path / "ledger.jsonl"
    existing = tmp_path / "existing.json"
    canonical.write_text(json.dumps(receipt(canonical=True)))
    generated.write_text(json.dumps(receipt()))
    ledger.write_bytes(Path(canonical_path(root=find_root(__file__))).read_bytes())
    existing.write_text("retained earlier report\n")
    paths = {"canonical": canonical, "generated": generated, "ledger": ledger,
             "existing": existing}
    before = {key: path.read_bytes() for key, path in paths.items()}
    if destination == "symlink":
        output = tmp_path / "linked-output.json"
        output.symlink_to(canonical)
    else:
        output = paths[destination]
    run = subprocess.run([sys.executable, str(SCRIPT), "--canonical", str(canonical),
                          "--generated", str(generated), "--canonical-ledger", str(ledger),
                          "--out", str(output)], capture_output=True, text=True)
    assert run.returncode == 2, run.stdout + run.stderr
    assert {key: path.read_bytes() for key, path in paths.items()} == before


def census_fixture():
    instance = {"task_id": "8738d400fb96", "rule_task_id": "8738d400fb96",
                "rule_file": "data/canonical/puzzles.jsonl", "train": [pair(3), pair(1)], "test": [pair(0)]}
    manifest = {"task_id": "8738d400fb96", "files": [
        {"library_path": "generators/8738d400fb96/generator.py", "sha256": "a"*64},
        {"library_path": "shared/data/canonical/puzzles.jsonl", "sha256": AUTHORITY["ledger_sha256"]}]}
    return {"schema": "arcpuzzles-lesson-census-v1", "task_id": "8738d400fb96",
            "rule_task_id": instance["rule_task_id"], "rule_file": instance["rule_file"],
            "generator_sha256": "a"*64, "rule_callable_sha256": "b"*64,
            "rule_source_sha256": AUTHORITY["program_sha256"], "declared_rule_hash": AUTHORITY["rule_hash"],
            "runtime_manifest": manifest,
            "runtime_manifest_sha256": hashlib.sha256((json.dumps(manifest,indent=2)+"\n").encode()).hexdigest(),
            "status": "no_contract", "production_status": "no_contract", "rotation_status": "not_requested",
            "errors": [], "execution": {"timed_out": False, "exit_code": 0},
            "sampler": {"bands": ["easy"], "n_demos": 2, "n_queries": 1, "per_band": 1, "rotate_query": False},
            "summary": {"requested": 1, "materialized": 1, "materialization_errors": 0,
                        "scoring_errors": 0, "rotation_scoring_errors": 0, "pairs": 3, "rotations": 0},
            "lessons": [{"band": "easy", "index": 0, "instance": instance,
                         "instance_sha256": digest(instance), "errors": [], "rotations": []}]}


def test_official_census_requires_explicit_adapter_and_valid_source_manifest():
    data = census_fixture()
    with pytest.raises(ValueError): tool.analyze(receipt(canonical=True),data)
    result = tool.analyze(receipt(canonical=True),data,adapter=tool.ADAPTER)
    assert result["status"] == "observed_support_in_each_band"
    wrong = deepcopy(data)
    wrong["generator_sha256"] = "f"*64
    with pytest.raises(ValueError): tool.analyze(receipt(canonical=True),wrong,adapter=tool.ADAPTER)


def test_official_census_missing_output_or_population_never_passes():
    for damage in ("label", "count", "instance"):
        data = census_fixture()
        if damage == "label": data["lessons"][0]["instance"]["test"][0].pop("output")
        elif damage == "count": data["summary"]["materialized"] = 0
        else: data["lessons"][0]["instance_sha256"] = "0"*64
        with pytest.raises(ValueError): tool.analyze(receipt(canonical=True),data,adapter=tool.ADAPTER)
