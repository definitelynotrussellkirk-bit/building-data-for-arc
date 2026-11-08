"""Focused checks for the proposed episode-level mapping-order prototype."""
from __future__ import annotations

from functools import cache
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

from reviewer_support import find_root, load_selected_generator


TASK_ID = "d5178d26d905"
ROOT = find_root(__file__)
GENERATOR, SELECTED_SOURCE, _SOURCE_SHA = load_selected_generator(TASK_ID, root=ROOT)
MANIFEST = ROOT / "RUNTIME_MANIFEST.json"
if MANIFEST.is_file():
    identity = f"generators/{TASK_ID}/workspace/parametric/prototype.py"
    entries = [
        row
        for row in json.loads(MANIFEST.read_text())["files"]
        if row.get("library_path") == identity
    ]
    entries.sort(key=lambda row: row.get("runtime_path") == identity)
    assert entries, "portable runtime must retain the parametric prototype"
    PROTOTYPE_PATH = ROOT / entries[0]["runtime_path"]
else:
    PROTOTYPE_PATH = SELECTED_SOURCE.parent / "workspace/parametric/prototype.py"


@cache
def prototype():
    assert PROTOTYPE_PATH.is_file(), "mapping-order prototype is missing"
    spec = importlib.util.spec_from_file_location(
        "d5178d26d905_mapping_order_prototype",
        PROTOTYPE_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parameter_contract_and_seed_choice_are_episode_level():
    p = prototype()
    assert p.PARAMETER_NAME == "special_mapping_order"
    assert p.ALLOWED_MAPPING_ORDERS == ("top_to_bottom", "bottom_to_top")
    assert p.DEFAULT_MAPPING_ORDER == "top_to_bottom"
    assert {p.choose_parameters(seed)[p.PARAMETER_NAME] for seed in range(8)} == {
        "top_to_bottom",
        "bottom_to_top",
    }
    assert p.choose_parameters(17) == p.choose_parameters(17)
    with pytest.raises(TypeError, match="episode_seed"):
        p.choose_parameters(True)


def test_shared_inputs_are_lawful_and_distinguish_both_exact_racket_rules():
    p = prototype()
    programs = {order: p.render_program(order) for order in p.ALLOWED_MAPPING_ORDERS}
    assert programs["top_to_bottom"] != programs["bottom_to_top"]
    assert "(reverse" not in programs["top_to_bottom"]
    assert "(reverse" in programs["bottom_to_top"]

    with p.RacketBridge() as bridge:
        for pair_index in range(4):
            grid = p.build_input(23, pair_index)
            assert GENERATOR.self_check(grid) == []
            outputs = {
                order: p.execute(grid, program, bridge)
                for order, program in programs.items()
            }
            assert outputs["top_to_bottom"] == GENERATOR.rule_mirror(grid)
            assert outputs["top_to_bottom"] != outputs["bottom_to_top"]


def test_materialized_rule_files_match_rendered_programs():
    p = prototype()
    rule_dir = PROTOTYPE_PATH.parent / "rules"
    for order in p.ALLOWED_MAPPING_ORDERS:
        path = rule_dir / f"{order}.rkt"
        assert path.is_file()
        assert path.read_text() == p.render_program(order)
        assert p.sha256_text(path.read_text()) == p.rule_sha256(order)


def test_complete_episodes_use_one_rule_and_public_queries_hide_answers():
    p = prototype()
    with p.RacketBridge() as bridge:
        for order in p.ALLOWED_MAPPING_ORDERS:
            episode = p.generate_episode(
                23,
                special_mapping_order=order,
                n_train=3,
                n_test=1,
                bridge=bridge,
            )
            assert episode["parameters"] == {"special_mapping_order": order}
            assert len(episode["train"]) == 3
            assert len(episode["test"]) == 1
            assert all(item["program_sha256"] == episode["program_sha256"] for item in episode["execution"])
            assert all(item["matches_selected_rule"] for item in episode["execution"])
            rival = next(value for value in p.ALLOWED_MAPPING_ORDERS if value != order)
            assert all(
                p.execute(pair["input"], p.render_program(rival), bridge) != pair["output"]
                for pair in episode["train"]
            )
            public = p.public_challenge(episode)
            assert set(public) == {"schema", "train", "test"}
            assert public["train"] == episode["train"]
            assert public["test"] == [{"input": episode["test"][0]["input"]}]
            encoded = json.dumps(public)
            assert "special_mapping_order" not in encoded
            assert "program" not in encoded


def test_cli_materializes_both_rules_and_complete_public_private_episodes(tmp_path):
    p = prototype()
    out = tmp_path / "parametric-evidence"
    result = subprocess.run(
        [sys.executable, str(PROTOTYPE_PATH), "--seed", "23", "--out", str(out)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    receipt = json.loads((out / "receipt.json").read_text())
    assert receipt["status"] == "proposed_prototype"
    assert receipt["complete_episodes"] == 2
    assert receipt["all_labels_executed_in_racket"] is True
    assert receipt["all_demonstrations_refute_other_setting"] is True
    for index, order in enumerate(p.ALLOWED_MAPPING_ORDERS):
        public = json.loads((out / f"public-{index}.json").read_text())
        private = json.loads((out / f"private-{index}.json").read_text())
        assert private["parameters"] == {"special_mapping_order": order}
        assert len(public["train"]) == 3
        assert len(public["test"]) == 1
        assert set(public["test"][0]) == {"input"}
        assert (out / f"rule-{index}.rkt").read_text() == private["program"]
