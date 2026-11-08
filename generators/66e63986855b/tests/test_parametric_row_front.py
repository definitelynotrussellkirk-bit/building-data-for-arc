"""Focused tests for the proposed row-front parametric rule prototype."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import find_root


TASK_ID = "66e63986855b"
TASK_ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE_PATH = TASK_ROOT / "workspace" / "parametric" / "prototype.py"


def _load_prototype():
    assert PROTOTYPE_PATH.is_file(), "row-front parametric prototype is not implemented"
    spec = importlib.util.spec_from_file_location(
        "parametric_row_front_66e63986855b", PROTOTYPE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_rule() -> str:
    root = find_root(__file__)
    ledger = root / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with ledger.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row["program_solution"]
    raise AssertionError(f"canonical row {TASK_ID} not found")


def test_parameter_contract_and_deterministic_episode_settings():
    prototype = _load_prototype()
    assert prototype.PARAMETER_SPECS == {
        "fill_extent": {
            "values": ("reflected", "to_axis"),
            "default": "reflected",
        },
        "source_policy": {
            "values": ("clear", "retain"),
            "default": "clear",
        },
    }
    expected = [
        {"fill_extent": "reflected", "source_policy": "clear"},
        {"fill_extent": "to_axis", "source_policy": "clear"},
        {"fill_extent": "reflected", "source_policy": "retain"},
        {"fill_extent": "to_axis", "source_policy": "retain"},
    ]
    assert [prototype.parameters_for_seed(seed) for seed in range(4)] == expected
    assert prototype.parameters_for_seed(4) == expected[0]
    with pytest.raises(ValueError):
        prototype.parameters_for_seed(-1)
    with pytest.raises(ValueError):
        prototype.parameters_for_seed(True)


def test_materialized_rules_are_guarded_and_canonical_default_is_byte_exact():
    prototype = _load_prototype()
    canonical = _canonical_rule()
    default = prototype.materialize_rule(
        fill_extent="reflected", source_policy="clear"
    )
    axis_clear = prototype.materialize_rule(
        fill_extent="to_axis", source_policy="clear"
    )
    mirror_retain = prototype.materialize_rule(
        fill_extent="reflected", source_policy="retain"
    )
    axis_retain = prototype.materialize_rule(
        fill_extent="to_axis", source_policy="retain"
    )

    assert default == canonical
    assert axis_clear != canonical
    assert mirror_retain != canonical
    assert axis_retain != canonical
    assert "(end maxc)" in axis_clear
    assert "(end (- (* 2 maxc) rc))" not in axis_clear
    assert "(cellmap g (r c v) 0)" in axis_clear
    assert "(end (- (* 2 maxc) rc))" in mirror_retain
    assert "(cellmap g (r c v) 0)" not in mirror_retain
    assert "                     g\n" in mirror_retain
    assert "(end maxc)" in axis_retain
    assert "(cellmap g (r c v) 0)" not in axis_retain

    with pytest.raises(ValueError):
        prototype.materialize_rule(fill_extent="beyond", source_policy="clear")
    with pytest.raises(ValueError):
        prototype.materialize_rule(fill_extent="reflected", source_policy="overlay")


def test_complete_episodes_have_fixed_settings_and_four_distinct_queries():
    prototype = _load_prototype()
    seen_settings = set()
    for seed in range(4):
        episode = prototype.build_episode(
            seed=seed,
            difficulty="medium",
            start_index=0,
            n_train=3,
            n_test=4,
            labeler=prototype.apply_python,
        )
        parameters = prototype.parameters_for_seed(seed)
        seen_settings.add(tuple(parameters.items()))
        assert episode["meta"]["parameters"] == parameters
        assert episode["meta"]["parameter_scope"] == "chosen once per episode"
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 4
        pairs = [*episode["train"], *episode["test"]]
        assert len({prototype.grid_sha256(pair["input"]) for pair in pairs}) == 7
        assert all(pair["output"] == prototype.apply_python(pair["input"], parameters)
                   for pair in pairs)
        findings = prototype.query_identifiability_findings(episode)
        assert findings == []
        records = episode["meta"]["query_identifiability"]
        assert len(records) == 4
        assert all(record["identifiable_from_demonstrations"] for record in records)
    assert len(seen_settings) == 4


def test_public_projection_is_strict_and_query_labels_do_not_drive_identifiability():
    prototype = _load_prototype()
    episode = prototype.build_episode(
        seed=3,
        difficulty="hard",
        start_index=5,
        n_train=3,
        n_test=4,
        labeler=prototype.apply_python,
    )
    before = prototype.query_identifiability_findings(episode)
    poisoned = json.loads(json.dumps(episode))
    for pair in poisoned["test"]:
        pair["output"] = [[9]]
    assert prototype.query_identifiability_findings(poisoned) == before == []

    public = prototype.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    serialized = json.dumps(public, sort_keys=True)
    for secret in (
        "meta", "parameters", "fill_extent", "source_policy",
        "reflected", "to_axis", "clear", "retain", "racket",
    ):
        assert secret not in serialized


def test_exact_racket_rules_match_independent_python_on_every_setting():
    prototype = _load_prototype()
    generator, _, _ = prototype.load_generator()
    grid = generator.generate(314159, 11, difficulty="hard")
    records = prototype.racket_python_parity(grid)
    assert len(records) == 4
    assert all(record["matches"] for record in records)
    assert {tuple(record["parameters"].items()) for record in records} == {
        tuple(setting.items()) for setting in prototype.SETTINGS
    }
    assert len({record["output_sha256"] for record in records}) == 4


@pytest.fixture(scope="module")
def final_evidence_report():
    prototype = _load_prototype()
    return prototype.build_evidence(
        seeds=[0, 1, 2, 3],
        difficulty="medium",
        start_index=0,
        n_train=3,
        n_test=4,
    )


def test_racket_backed_evidence_covers_all_settings_canonical_pairs_and_four_queries(
    final_evidence_report,
):
    report = final_evidence_report
    assert report["status"] == "proposed_unapproved"
    assert report["passed"] is True
    assert report["canonical_authority_changed"] is False
    assert report["default_program_byte_identical"] is True
    assert report["counts"]["settings_materialized"] == 4
    assert report["counts"]["episodes"] == 4
    assert report["counts"]["distinct_settings_demonstrated"] == 4
    assert report["counts"]["canonical_pairs"] == 4
    assert report["counts"]["canonical_passed"] == 4
    assert report["counts"]["train_pairs"] == 12
    assert report["counts"]["query_pairs"] == 16
    assert report["counts"]["distinct_inputs"] == 28
    assert report["counts"]["python_parity_passed"] == 28
    assert report["counts"]["query_identifiable"] == 16
    assert report["counts"]["query_checks"] == 16
    assert report["setting_difference_witness"]["distinct_output_count"] == 4
    assert all(record["passed"] for record in report["canonical_checks"])
    assert all(
        len(record["episode"]["test"]) == 4
        and record["query_identifiability_findings"] == []
        and all(check["python_parity"] for check in record["pair_checks"])
        for record in report["episodes"]
    )


def test_public_name_depends_only_on_visible_bytes_and_writer_refuses_overwrite(
    tmp_path, final_evidence_report
):
    prototype = _load_prototype()
    episode = final_evidence_report["episodes"][0]["episode"]
    original_name = prototype.public_artifact_name(episode)

    private_mutation = json.loads(json.dumps(episode))
    private_mutation["meta"]["seed"] = 999999
    private_mutation["meta"]["parameters"] = {
        "fill_extent": "to_axis",
        "source_policy": "retain",
    }
    for pair in private_mutation["test"]:
        pair["output"] = [[9]]
    assert prototype.public_artifact_name(private_mutation) == original_name

    visible_mutation = json.loads(json.dumps(episode))
    visible_mutation["test"][0]["input"][0][0] = (
        visible_mutation["test"][0]["input"][0][0] + 1
    ) % 10
    assert prototype.public_artifact_name(visible_mutation) != original_name

    private_dir = tmp_path / "private"
    public_dir = tmp_path / "public"
    manifest = prototype.write_evidence(
        out_dir=private_dir,
        public_dir=public_dir,
        report=final_evidence_report,
    )
    assert manifest["passed"] is True
    public_files = sorted(public_dir.iterdir())
    assert len(public_files) == 4
    assert {path.name for path in public_files} == {
        record["public_filename"] for record in final_evidence_report["episodes"]
    }
    for path in public_files:
        assert path.name.startswith("challenge_")
        assert len(path.stem.removeprefix("challenge_")) == 64
        payload = json.loads(path.read_text())
        assert set(payload) == {"train", "test"}
        assert all(set(pair) == {"input", "output"} for pair in payload["train"])
        assert all(set(pair) == {"input"} for pair in payload["test"])
        serialized = path.read_text()
        for secret in (
            "seed", "parameters", "fill_extent", "source_policy",
            "reflected", "to_axis", "retain", "racket_source",
        ):
            assert secret not in serialized

    setting_map = json.loads((private_dir / "private" / "setting-map.json").read_text())
    public_ids = [row["public_id"] for row in setting_map]
    assert public_ids == sorted(public_ids)

    with pytest.raises(FileExistsError):
        prototype.write_evidence(
            out_dir=private_dir,
            public_dir=public_dir,
            report=final_evidence_report,
        )


def test_writer_rejects_duplicate_visible_public_payloads(tmp_path, final_evidence_report):
    prototype = _load_prototype()
    duplicate_report = json.loads(json.dumps(final_evidence_report))
    first = duplicate_report["episodes"][0]
    second = duplicate_report["episodes"][1]
    second["episode"] = json.loads(json.dumps(first["episode"]))
    second["public_id"] = first["public_id"]
    second["public_filename"] = first["public_filename"]

    with pytest.raises(ValueError, match="duplicate visible public payload"):
        prototype.write_evidence(
            out_dir=tmp_path / "private",
            public_dir=tmp_path / "public",
            report=duplicate_report,
        )


def test_duplicate_only_sampler_fails_after_the_explicit_retry_budget(monkeypatch):
    prototype = _load_prototype()

    class DuplicateOnlyGenerator:
        VERSION = "duplicate-only-test"

        @staticmethod
        def generate(seed, sample_index, difficulty="medium"):
            del seed, sample_index, difficulty
            return [[1, 0], [0, 0]]

    generator_path = prototype.ROOT / "generators" / TASK_ID / "generator.py"
    monkeypatch.setattr(
        prototype,
        "load_generator",
        lambda: (DuplicateOnlyGenerator(), generator_path, "0" * 64),
    )

    with pytest.raises(
        RuntimeError,
        match=r"sampled only 1 distinct inputs after 7 attempts; requested 7",
    ):
        prototype.build_episode(
            seed=0,
            difficulty="medium",
            start_index=0,
            n_train=3,
            n_test=4,
            max_attempts=7,
            labeler=lambda grid, parameters: grid,
        )


def test_writer_rolls_back_private_directory_if_public_install_fails(
    tmp_path, final_evidence_report, monkeypatch
):
    prototype = _load_prototype()
    import os

    out_dir = tmp_path / "private"
    public_dir = tmp_path / "public"
    real_replace = os.replace
    calls = 0

    def fail_second_replace(source, destination):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("simulated public-directory install failure")
        return real_replace(source, destination)

    monkeypatch.setattr(os, "replace", fail_second_replace)
    with pytest.raises(OSError, match="simulated public-directory install failure"):
        prototype.write_evidence(
            out_dir=out_dir,
            public_dir=public_dir,
            report=final_evidence_report,
        )

    assert not out_dir.exists()
    assert not public_dir.exists()
