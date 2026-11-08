"""Proposed output-policy prototype; separate from canonical repair coverage."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root

HOME = Path(__file__).resolve().parents[1]
SOURCE = HOME / "workspace/parametric/prototype.py"


@pytest.fixture(scope="module")
def proto():
    if not SOURCE.is_file():
        pytest.skip("implementation absent; test_prototype_exists supplies the red assertion")
    spec = importlib.util.spec_from_file_location("output_policy_prototype", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_prototype_exists():
    assert SOURCE.is_file(), "the proposed output-policy prototype is not implemented"


def test_canonical_setting_preserves_exact_program_and_all_canonical_answers(proto):
    assert proto.materialize_rule("move", "donor") == proto.canonical_rule()
    with proto.RacketBridge(timeout=20) as bridge:
        for pair in canonical_pairs(proto.TASK_ID, root=find_root(__file__)):
            assert proto.execute(bridge, proto.materialize_rule(), pair["input"]) == pair["output"]


def test_every_policy_has_exact_role_semantics_and_preserves_other_cells(proto):
    gen, _, _ = proto.selected_generator()
    with proto.RacketBridge(timeout=20) as bridge:
        for index in range(6):
            grid = gen.generate(731, index)
            before = deepcopy(grid)
            parsed = gen.analyze_grid(grid)
            outputs = []
            for donor_policy, fill_policy in proto.SETTINGS:
                expected = deepcopy(grid)
                for r, c in parsed["donor_cells"]:
                    expected[r][c] = parsed["background"] if donor_policy == "move" else parsed["donor"]
                for r, c in parsed["missing"]:
                    expected[r][c] = parsed[fill_policy]
                actual = proto.execute(bridge, proto.materialize_rule(donor_policy, fill_policy), grid)
                assert actual == expected
                outputs.append(json.dumps(actual))
            assert len(set(outputs)) == 4
            assert grid == before


def test_episode_replay_parameter_identification_and_public_projection(proto):
    with proto.RacketBridge(timeout=20) as bridge:
        for setting in proto.SETTINGS:
            episode = proto.build_episode(41, 2, setting=setting, bridge=bridge)
            assert episode == proto.build_episode(41, 2, setting=setting, bridge=bridge)
            public, private = episode["public"], episode["private"]
            assert set(public) == {"train", "test"}
            assert len(public["train"]) == 3 and len(public["test"]) == 1
            assert all(set(pair) == {"input", "output"} for pair in public["train"])
            assert set(public["test"][0]) == {"input"}
            assert private["parameters"] == dict(zip(("donor_policy", "fill_policy"), setting))
            assert private["sample_indices"] == [8, 9, 10, 11]
            assert len(private["rival_checks"]) == 3
            assert all(check["refuted_by_demo_indices"] for check in private["rival_checks"])
            assert all(i < len(public["train"]) for check in private["rival_checks"]
                       for i in check["refuted_by_demo_indices"])
        seeded = [proto.choose_setting(seed) for seed in range(32)]
        assert set(seeded) == set(proto.SETTINGS)


def test_evidence_is_complete_source_bound_and_public_files_are_answer_free(proto, tmp_path):
    summary = proto.write_evidence(tmp_path / "run", seed=73, episodes_per_setting=1)
    assert summary["episode_count"] == 4
    assert summary["same_input_distinct_outputs"] == 4
    manifest = json.loads((tmp_path / "run/private/manifest.json").read_text())
    assert len(manifest["rules"]) == 4
    for row in manifest["rules"]:
        body = (tmp_path / "run" / row["path"]).read_bytes()
        assert hashlib.sha256(body).hexdigest() == row["sha256"]
    for row in manifest["episodes"]:
        public = json.loads((tmp_path / "run" / row["public_path"]).read_text())
        private = json.loads((tmp_path / "run" / row["private_path"]).read_text())
        assert set(public) == {"train", "test"}
        assert all(set(q) == {"input"} for q in public["test"])
        assert private["parameter_selection"] == "deterministic_seed"
        assert tuple(private["parameters"][key] for key in ("donor_policy", "fill_policy")) == proto.choose_setting(private["seed"])
    assert "prototype_sha256" in manifest["source"]
    assert "generator_sha256" in manifest["source"]
    assert "prelude_sha256" in manifest["source"]


def test_standalone_seed_selection_retains_automatic_replay_metadata(proto):
    episode = proto.build_episode(29)
    assert episode["private"]["parameter_selection"] == "deterministic_seed"
    assert episode["private"]["parameters"] == dict(zip(
        ("donor_policy", "fill_policy"), proto.choose_setting(29)))


@pytest.mark.parametrize("setting", [("erase", "donor"), ("move", "red"), (True, "target")])
def test_unsupported_settings_fail(proto, setting):
    with pytest.raises(ValueError):
        proto.materialize_rule(*setting)


@pytest.mark.parametrize("seed,index", [(True, 0), (1, -1), (1, True)])
def test_invalid_replay_controls_fail(proto, seed, index):
    with pytest.raises((TypeError, ValueError)):
        proto.build_episode(seed, index)
