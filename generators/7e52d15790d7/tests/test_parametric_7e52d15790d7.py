from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "7e52d15790d7"
ROOT = find_root(__file__)
PROTO_PATH = Path(__file__).resolve().parents[1] / "workspace/parametric/prototype.py"


def _load_prototype():
    spec = importlib.util.spec_from_file_location("_parametric_7e52d15790d7_test", PROTO_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prototype = _load_prototype()


def _canonical_program() -> str:
    rows = []
    with canonical_path(ROOT).open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    rows.append(row)
    assert len(rows) == 1
    return rows[0]["program_solution"]


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


def test_default_program_is_exact_canonical_and_all_settings_are_guarded():
    assert prototype.DEFAULT_SETTINGS == {"metric": "perimeter", "direction": "descending"}
    assert prototype.program_for(prototype.DEFAULT_SETTINGS) == _canonical_program()
    programs = [prototype.program_for(settings) for settings in prototype.SETTINGS]
    assert len(set(programs)) == 4
    assert all(program.startswith("(rule!") for program in programs)
    with pytest.raises(ValueError):
        prototype.program_for({"metric": "bbox", "direction": "descending"})
    with pytest.raises(ValueError):
        prototype.program_for({"metric": "perimeter", "direction": "sideways"})
    with pytest.raises(ValueError):
        prototype.program_for({"metric": "perimeter", "direction": "descending", "extra": 1})


def test_demo_and_query_counts_are_independent_and_first_query_is_prefix_stable():
    small = prototype.generate_claims(17, prototype.DEFAULT_SETTINGS, demos=2, queries=1)
    large = prototype.generate_claims(17, prototype.DEFAULT_SETTINGS, demos=6, queries=4)
    assert len(small["train"]) == 2 and len(small["test"]) == 1
    assert len(large["train"]) == 6 and len(large["test"]) == 4
    assert [pair["input"] for pair in small["train"]] == [
        pair["input"] for pair in large["train"][:2]
    ]
    assert small["test"][0]["input"] == large["test"][0]["input"]
    all_inputs = [pair["input"] for pair in large["train"] + large["test"]]
    assert len({_frozen(grid) for grid in all_inputs}) == len(all_inputs)
    for bad in (True, 1.5, "3", 1, 7):
        with pytest.raises(ValueError):
            prototype.generate_claims(17, prototype.DEFAULT_SETTINGS, demos=bad, queries=4)
    for bad in (True, 0, 5):
        with pytest.raises(ValueError):
            prototype.generate_claims(17, prototype.DEFAULT_SETTINGS, demos=3, queries=bad)


def test_two_demonstrations_identify_each_setting_and_four_queries_are_matched():
    episodes = [prototype.generate_claims(29, settings, demos=2, queries=4) for settings in prototype.SETTINGS]
    matched_inputs = [pair["input"] for pair in episodes[0]["train"] + episodes[0]["test"]]
    for settings, episode in zip(prototype.SETTINGS, episodes):
        assert [pair["input"] for pair in episode["train"] + episode["test"]] == matched_inputs
        certificate = prototype.lesson_certificate(episode)
        assert certificate["identifiable"] is True
        assert certificate["survivors"] == [prototype.setting_name(settings)]
        assert len({_frozen(pair["input"]) for pair in episode["test"]}) == 4
    for query_index in range(4):
        outputs = {_frozen(episode["test"][query_index]["output"]) for episode in episodes}
        assert len(outputs) == 4


def test_third_query_is_substantive_30x30_and_all_outputs_remain_bounded():
    episode = prototype.generate_claims(41, prototype.DEFAULT_SETTINGS, demos=3, queries=4)
    grid = episode["test"][2]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    nonzero = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    assert len(nonzero) >= 70
    assert {0, 29} <= {r for r, _ in nonzero}
    assert {0, 29} <= {c for _, c in nonzero}
    for settings in prototype.SETTINGS:
        output = prototype.transform(grid, settings)
        assert 1 <= len(output) <= 30
        assert 1 <= len(output[0]) <= 30


def test_racket_matrix_matches_python_and_public_bytes_ignore_private_fields():
    result = prototype.make_episodes(53, demos=2, queries=4)
    assert result["runtime_identity"]["protected"] is True
    assert len(result["episodes"]) == 4
    for episode in result["episodes"]:
        assert episode["certificate"]["identifiable"] is True
        assert episode["racket_parity"] == {"pairs": 6, "settings": 4, "matches": 24}
        public = public_challenge_bytes(episode)
        assert b'"settings"' not in public and b'"program"' not in public
        assert b'"output"' not in json.dumps(json.loads(public)["test"], sort_keys=True).encode()
        mutated = dict(episode)
        mutated["settings"] = {"metric": "private-change", "direction": "private-change"}
        mutated["program_solution"] = "private-change"
        assert public_challenge_id(mutated) == public_challenge_id(episode)


def test_materialized_batch_verifies_and_rejects_tampering_and_extras(tmp_path):
    out = tmp_path / "batch"
    report = prototype.materialize_batch(seed=67, demos=2, queries=4, out=out)
    assert report["episodes"] == 4
    verified = prototype.verify_batch(out)
    assert verified["episodes"] == 4
    assert verified["racket_pairs"] == 24

    extra = tmp_path / "extra"
    shutil.copytree(out, extra)
    (extra / "unexpected.txt").write_text("not declared\n", encoding="utf-8")
    with pytest.raises(ValueError, match="unexpected"):
        prototype.verify_batch(extra)

    tampered = tmp_path / "tampered"
    shutil.copytree(out, tampered)
    public_path = next((tampered / "public").glob("*.json"))
    payload = json.loads(public_path.read_text(encoding="utf-8"))
    payload["settings"] = {"metric": "leak"}
    public_path.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    with pytest.raises(ValueError):
        prototype.verify_batch(tampered)

    if hasattr(Path, "symlink_to"):
        linked = tmp_path / "linked"
        shutil.copytree(out, linked)
        (linked / "public-link.json").symlink_to(next((linked / "public").glob("*.json")))
        with pytest.raises(ValueError, match="symlink"):
            prototype.verify_batch(linked)


def _canonical_json_write(path, value):
    raw = (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def _mutate_private_and_rehash(batch, field, value):
    manifest_path = batch / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    row = manifest["episodes"][0]
    private_path = batch / row["private_path"]
    private = json.loads(private_path.read_text(encoding="utf-8"))
    private[field] = value
    digest = _canonical_json_write(private_path, private)
    row["private_sha256"] = digest
    manifest["files"][row["private_path"]] = digest
    _canonical_json_write(manifest_path, manifest)


def test_verifier_rejects_forged_source_runtime_parity_and_manifest_metadata(tmp_path):
    original = tmp_path / "batch"
    prototype.materialize_batch(seed=71, demos=2, queries=4, out=original)

    for field, value in (
        ("source", {"forged": True}),
        ("runtime_identity", {"protected": True, "forged": True}),
        ("racket_parity", {"pairs": 6, "settings": 4, "matches": 999}),
    ):
        changed = tmp_path / f"private-{field}"
        shutil.copytree(original, changed)
        _mutate_private_and_rehash(changed, field, value)
        with pytest.raises(ValueError):
            prototype.verify_batch(changed)

    changed = tmp_path / "manifest-source"
    shutil.copytree(original, changed)
    manifest_path = changed / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["source"] = {"forged": True}
    _canonical_json_write(manifest_path, manifest)
    with pytest.raises(ValueError):
        prototype.verify_batch(changed)

    changed = tmp_path / "manifest-counts"
    shutil.copytree(original, changed)
    manifest_path = changed / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["counts"] = {"episodes": 4, "demos": 6, "queries": 1}
    _canonical_json_write(manifest_path, manifest)
    with pytest.raises(ValueError):
        prototype.verify_batch(changed)


def test_verifier_rejects_empty_directories_and_declared_unreferenced_files(tmp_path):
    original = tmp_path / "batch"
    prototype.materialize_batch(seed=73, demos=2, queries=4, out=original)

    changed = tmp_path / "empty-directory"
    shutil.copytree(original, changed)
    (changed / "public" / "empty").mkdir()
    with pytest.raises(ValueError):
        prototype.verify_batch(changed)

    changed = tmp_path / "orphan"
    shutil.copytree(original, changed)
    manifest_path = changed / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source = changed / manifest["episodes"][0]["private_path"]
    orphan = changed / "private" / "orphan.json"
    shutil.copyfile(source, orphan)
    manifest["files"]["private/orphan.json"] = hashlib.sha256(orphan.read_bytes()).hexdigest()
    _canonical_json_write(manifest_path, manifest)
    with pytest.raises(ValueError):
        prototype.verify_batch(changed)
