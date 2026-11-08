from __future__ import annotations

import hashlib
import importlib.util
import inspect
import json
import re
from pathlib import Path

import pytest

from reviewer_support import (
    canonical_pairs,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "51e59bb53cac"
ROOT = find_root(__file__)
TASK_HOME = ROOT / "generators" / TASK_ID
PROTOTYPE_PATH = TASK_HOME / "workspace" / "parametric" / "prototype.py"


def _prototype():
    if not PROTOTYPE_PATH.is_file():
        pytest.fail("task-local swap-scope prototype has not been implemented")
    spec = importlib.util.spec_from_file_location(
        "parametric_swap_scope_51e59bb53cac", PROTOTYPE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _generator():
    return load_selected_generator(TASK_ID, root=ROOT)[0]


def test_materialized_rules_preserve_default_and_derive_one_exterior_variant():
    mod = _prototype()
    source = mod.canonical_rule()
    normalized = " ".join(source.split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == "6efb83adf2b2"
    assert mod.SWAP_SCOPES == ("interior", "exterior")
    assert mod.DEFAULT_SWAP_SCOPE == "interior"
    assert mod.rule_text("interior") == source
    expected_exterior = source.replace(
        mod.INTERIOR_CONDITION,
        mod.EXTERIOR_CONDITION,
    )
    assert source.count(mod.INTERIOR_CONDITION) == 1
    assert expected_exterior != source
    assert mod.rule_text("exterior") == expected_exterior
    assert (mod.HERE / "rules" / "interior.rkt").read_text() == source
    assert (mod.HERE / "rules" / "exterior.rkt").read_text() == expected_exterior


def test_matching_racket_executes_every_setting_and_default_matches_canonical_pairs():
    mod = _prototype()
    generator = _generator()
    with mod.RuleEngine() as engine:
        pairs = canonical_pairs(TASK_ID, root=ROOT)
        assert len(pairs) >= 4
        for pair in pairs:
            assert engine.apply(pair["input"], "interior") == pair["output"]

        grid = generator.generate(
            310,
            7,
            difficulty="hard",
            frame_anchor="edge",
            palette_kind="canonical",
        )
        before = json.loads(json.dumps(grid))
        interior = engine.apply(grid, "interior")
        exterior = engine.apply(grid, "exterior")

    assert grid == before
    assert interior == generator.rule_mirror(grid)
    assert interior == mod.apply_python(grid, "interior")
    assert exterior == mod.apply_python(grid, "exterior")
    assert interior != exterior
    analysis = generator._analysis(grid)
    color_a, color_b = analysis["colors"]
    global_swap = [
        [
            color_b if value == color_a else color_a if value == color_b else value
            for value in row
        ]
        for row in grid
    ]
    global_key = tuple(map(tuple, global_swap))
    assert global_key not in {tuple(map(tuple, interior)), tuple(map(tuple, exterior))}


def test_episode_fixes_scope_and_each_query_is_identified_from_demos_only():
    mod = _prototype()
    signature = inspect.signature(mod.identify_query)
    assert "swap_scope" not in signature.parameters
    assert "query_output" not in signature.parameters

    with mod.RuleEngine() as engine:
        episode = mod.generate_episode(
            17,
            swap_scope="exterior",
            demos=2,
            queries=4,
            engine=engine,
        )

    public = episode["public"]
    private = episode["private"]
    assert private["parameters"] == {"swap_scope": "exterior"}
    assert private["demos"] == 2
    assert private["queries"] == 4
    assert len(public["train"]) == 2
    assert len(public["test"]) == 4
    assert len(private["query_outputs"]) == 4
    assert len(set(private["input_sha256"])) == 6
    assert private["demo_only_survivors"] == ["exterior"]
    assert len(private["query_checks"]) == 4
    for check in private["query_checks"]:
        assert check["survivors"] == ["exterior"]
        assert check["mismatching_demo_indices"]["exterior"] == []
        assert check["mismatching_demo_indices"]["interior"]
        assert check["mismatching_demo_indices"]["global"]
        assert check["mismatching_demo_indices"]["identity"]
        assert set(check["query_prediction_sha256"]) == {"exterior"}
        assert "query_output" not in check


def test_same_seed_contrast_changes_outputs_not_inputs():
    mod = _prototype()
    with mod.RuleEngine() as engine:
        interior = mod.generate_episode(
            23,
            swap_scope="interior",
            demos=2,
            queries=4,
            engine=engine,
        )
        exterior = mod.generate_episode(
            23,
            swap_scope="exterior",
            demos=2,
            queries=4,
            engine=engine,
        )

    assert interior["private"]["input_sha256"] == exterior["private"]["input_sha256"]
    assert [p["input"] for p in interior["public"]["train"]] == [
        p["input"] for p in exterior["public"]["train"]
    ]
    assert [p["input"] for p in interior["public"]["test"]] == [
        p["input"] for p in exterior["public"]["test"]
    ]
    assert all(
        left["output"] != right["output"]
        for left, right in zip(interior["public"]["train"], exterior["public"]["train"])
    )
    assert all(
        left != right
        for left, right in zip(
            interior["private"]["query_outputs"],
            exterior["private"]["query_outputs"],
        )
    )
    assert public_challenge_id(interior["public"]) != public_challenge_id(exterior["public"])


def test_writer_uses_visible_only_opaque_public_ids(tmp_path):
    mod = _prototype()
    report = mod.write_bundle(
        tmp_path,
        seed=31,
        swap_scope="both",
        demos=2,
        queries=4,
    )

    assert report["status"] == "proposed prototype; no production approval"
    assert report["canonical_parity"]["passed"] == report["canonical_parity"]["total"]
    assert report["parameter_witness"]["outputs_differ"] is True
    assert len(report["episodes"]) == 2
    report_ids = [row["public_id"] for row in report["episodes"]]
    assert report_ids == sorted(report_ids)

    public_files = sorted((tmp_path / "public").glob("*.json"))
    private_files = sorted((tmp_path / "private" / "episodes").glob("*.json"))
    assert len(public_files) == len(private_files) == 2
    assert all(re.fullmatch(r"[0-9a-f]{64}\.json", path.name) for path in public_files)
    assert all("interior" not in path.name and "exterior" not in path.name for path in public_files)

    for path in public_files:
        payload = json.loads(path.read_text())
        assert set(payload) == {"train", "test"}
        assert len(payload["train"]) == 2
        assert len(payload["test"]) == 4
        assert all(set(pair) == {"input", "output"} for pair in payload["train"])
        assert all(set(pair) == {"input"} for pair in payload["test"])
        assert path.read_bytes() == public_challenge_bytes(payload)
        assert path.stem == public_challenge_id(payload)

    mapping = json.loads((tmp_path / "private" / "setting-map.json").read_text())
    assert set(mapping.values()) == {"interior", "exterior"}
    assert set(mapping) == {path.stem for path in public_files}
    assert (tmp_path / "summary.json").is_file()


def test_parameter_and_count_validation_is_strict():
    mod = _prototype()
    assert mod.choose_scope(41) == mod.choose_scope(41)
    assert mod.choose_scope(41) in mod.SWAP_SCOPES
    for bad_seed in (True, -1, 2**63):
        with pytest.raises((TypeError, ValueError)):
            mod.choose_scope(bad_seed)
    with pytest.raises(ValueError):
        mod.rule_text("global")
    for bad_count in (True, 0, 33, 1.5):
        with pytest.raises((TypeError, ValueError)):
            mod.generate_episode(1, swap_scope="interior", demos=bad_count, queries=4)
        with pytest.raises((TypeError, ValueError)):
            mod.generate_episode(1, swap_scope="interior", demos=2, queries=bad_count)
