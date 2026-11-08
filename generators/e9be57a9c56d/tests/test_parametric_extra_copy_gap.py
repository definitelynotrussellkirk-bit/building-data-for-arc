from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from reviewer_support import (
    canonical_pairs,
    find_root,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_HOME = Path(__file__).resolve().parents[1]
PROTOTYPE_PATH = TASK_HOME / "workspace" / "parametric" / "prototype.py"


def load_prototype():
    assert PROTOTYPE_PATH.is_file(), "parametric prototype has not been implemented"
    spec = importlib.util.spec_from_file_location(
        "e9be57a9c56d_parametric_extra_copy_gap", PROTOTYPE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def grid(*rows: str) -> list[list[int]]:
    widths = {len(row) for row in rows}
    assert len(widths) == 1
    return [[int(cell) for cell in row] for row in rows]


def catalog_rule_hash(program: str) -> str:
    return hashlib.sha256(" ".join(program.split()).encode("utf-8")).hexdigest()[:12]


def test_default_rule_is_exact_canonical_authority_and_replays_all_pairs():
    prototype = load_prototype()
    program = prototype.canonical_program()
    assert prototype.materialize_rule() == program
    assert prototype.materialize_rule(0) == program
    assert catalog_rule_hash(program) == "f8100feef807"

    pairs = canonical_pairs("e9be57a9c56d", root=find_root(__file__))
    assert pairs
    with prototype.RuleOracle() as oracle:
        for pair in pairs:
            assert oracle.apply(program, pair["input"]) == pair["output"]


def test_extra_gap_one_moves_non_anchor_copies_one_cell_per_chain_step():
    prototype = load_prototype()
    source = grid(
        "030020004000000",
        "000000000000000",
        "000000000000000",
        "000002200000000",
        "000002000000000",
        "000000000000000",
        "000000000000000",
    )
    canonical = grid(
        "030020004000000",
        "000000000000000",
        "000000000000000",
        "033002200044000",
        "030002000040000",
        "000000000000000",
        "000000000000000",
    )
    extra = grid(
        "030020004000000",
        "000000000000000",
        "000000000000000",
        "330002200004400",
        "300002000004000",
        "000000000000000",
        "000000000000000",
    )

    with prototype.RuleOracle() as oracle:
        assert oracle.apply(prototype.materialize_rule(0), source) == canonical
        assert oracle.apply(prototype.materialize_rule(1), source) == extra


def test_parameter_and_seed_validation_are_exact_not_truthy():
    prototype = load_prototype()
    assert prototype.choose_extra_copy_gap(0) == 0
    assert prototype.choose_extra_copy_gap(1) == 1
    assert prototype.choose_extra_copy_gap(12) == 0
    assert prototype.choose_extra_copy_gap(13) == 1

    for invalid in (True, -1, 2, 1.0, "1", None):
        with pytest.raises(ValueError):
            prototype.materialize_rule(invalid)
    for invalid_seed in (True, -1, 1.5, "3"):
        with pytest.raises(ValueError):
            prototype.choose_extra_copy_gap(invalid_seed)


def test_alternative_rule_is_deterministic_and_changes_the_authority():
    prototype = load_prototype()
    first = prototype.materialize_rule(1)
    second = prototype.materialize_rule(1)
    assert first == second
    assert first != prototype.canonical_program()
    assert catalog_rule_hash(first) != "f8100feef807"


def test_episode_holds_one_setting_and_four_distinct_queries():
    prototype = load_prototype()
    with prototype.RuleOracle() as oracle:
        episode = prototype.build_episode(
            seed=17,
            extra_copy_gap=1,
            demo_count=3,
            query_count=4,
            oracle=oracle,
        )
        public = episode["public"]
        private = episode["private"]
        assert set(public) == {"train", "test"}
        assert len(public["train"]) == 3
        assert len(public["test"]) == 4
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert all(set(pair) == {"input"} for pair in public["test"])
        assert private["parameters"] == {"extra_copy_gap": 1}
        assert private["selection"] == "explicit"
        assert len(private["query_outputs"]) == 4

        all_inputs = [pair["input"] for pair in public["train"] + public["test"]]
        assert len({repr(value) for value in all_inputs}) == 7
        assert all(1 <= len(value) <= 30 and 1 <= len(value[0]) <= 30 for value in all_inputs)

        selected = prototype.materialize_rule(1)
        opposite = prototype.materialize_rule(0)
        for pair in public["train"]:
            assert oracle.apply(selected, pair["input"]) == pair["output"]
        for pair, output, check in zip(
            public["test"], private["query_outputs"], private["per_query_checks"]
        ):
            assert oracle.apply(selected, pair["input"]) == output
            assert oracle.apply(opposite, pair["input"]) != output
            assert check["identified_from_demonstrations"] is True
            assert check["opposite_changes_query"] is True

        fit = private["rival_fit"]
        assert fit["basis"] == "demonstrations_only"
        assert fit["surviving_rivals"] == []
        assert fit["rivals"][0]["extra_copy_gap"] == 0
        assert fit["rivals"][0]["refuted_by_demo"]


def test_seeded_setting_is_selected_once_and_episode_replays_exactly():
    prototype = load_prototype()
    with prototype.RuleOracle() as oracle:
        even = prototype.build_episode(
            seed=18, extra_copy_gap=None, demo_count=3, query_count=2, oracle=oracle
        )
        again = prototype.build_episode(
            seed=18, extra_copy_gap=None, demo_count=3, query_count=2, oracle=oracle
        )
        odd = prototype.build_episode(
            seed=19, extra_copy_gap=None, demo_count=3, query_count=2, oracle=oracle
        )
    assert even == again
    assert even["private"]["parameters"] == {"extra_copy_gap": 0}
    assert odd["private"]["parameters"] == {"extra_copy_gap": 1}
    assert even["private"]["selection"] == "seeded_once"
    assert odd["private"]["selection"] == "seeded_once"


def test_episode_counts_and_parameter_values_fail_explicitly():
    prototype = load_prototype()
    invalid = [
        {"seed": 0, "extra_copy_gap": 0, "demo_count": 2, "query_count": 4},
        {"seed": 0, "extra_copy_gap": 0, "demo_count": 3, "query_count": 0},
        {"seed": 0, "extra_copy_gap": 0, "demo_count": True, "query_count": 4},
        {"seed": 0, "extra_copy_gap": 0, "demo_count": 3, "query_count": 17},
        {"seed": True, "extra_copy_gap": 0, "demo_count": 3, "query_count": 4},
        {"seed": 0, "extra_copy_gap": True, "demo_count": 3, "query_count": 4},
    ]
    for kwargs in invalid:
        with pytest.raises(ValueError):
            prototype.build_episode(**kwargs)


def test_every_sampled_input_executes_both_settings_without_dimension_change():
    prototype = load_prototype()
    with prototype.RuleOracle() as oracle:
        for selected_gap in (0, 1):
            episode = prototype.build_episode(
                seed=41 + selected_gap,
                extra_copy_gap=selected_gap,
                demo_count=4,
                query_count=8,
                oracle=oracle,
            )
            inputs = [
                pair["input"]
                for pair in episode["public"]["train"] + episode["public"]["test"]
            ]
            for source in inputs:
                for gap in (0, 1):
                    output = oracle.apply(prototype.materialize_rule(gap), source)
                    assert len(output) == len(source)
                    assert len(output[0]) == len(source[0])


def test_evidence_writer_uses_exact_visible_bytes_and_keeps_private_labels_out():
    prototype = load_prototype()
    with TemporaryDirectory() as temporary:
        output = Path(temporary) / "extra-gap-evidence"
        manifest = prototype.write_evidence(
            output,
            seeds=[10, 11],
            extra_copy_gaps=[0, 1],
            demo_count=3,
            query_count=4,
        )
        assert manifest == json.loads((output / "manifest.json").read_text())
        assert len(manifest["episodes"]) == 2
        assert [row["public_challenge_id"] for row in manifest["episodes"]] == sorted(
            row["public_challenge_id"] for row in manifest["episodes"]
        )

        for row in manifest["episodes"]:
            public_path = output / row["public_path"]
            private_path = output / row["private_path"]
            public = json.loads(public_path.read_text())
            private = json.loads(private_path.read_text())
            assert set(public) == {"train", "test"}
            assert all(set(pair) == {"input"} for pair in public["test"])
            assert private["public_challenge_id"] == public_challenge_id(public)
            assert public_path.name == f"challenge-{private['public_challenge_id']}.json"
            assert public_path.read_bytes() == public_challenge_bytes(public)
            assert len(private["episode_private"]["query_outputs"]) == 4
            assert "query_outputs" not in public

        for record in manifest["files"]:
            path = output / record["path"]
            assert path.is_file()
            assert hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"]

        assert (output / "private" / "rules" / "extra-copy-gap-0.rkt").read_text() == prototype.materialize_rule(0)
        assert (output / "private" / "rules" / "extra-copy-gap-1.rkt").read_text() == prototype.materialize_rule(1)
        verification = prototype.verify_evidence(output)
        assert verification["ok"] is True
        assert verification["episode_count"] == 2


def test_writer_fails_closed_on_existing_directory_and_duplicate_public_payloads():
    prototype = load_prototype()
    with TemporaryDirectory() as temporary:
        existing = Path(temporary) / "existing"
        existing.mkdir()
        with pytest.raises(FileExistsError):
            prototype.write_evidence(
                existing,
                seeds=[0],
                extra_copy_gaps=[0],
                demo_count=3,
                query_count=4,
            )

        duplicate = Path(temporary) / "duplicate"
        with pytest.raises(ValueError, match="duplicate visible payload"):
            prototype.write_evidence(
                duplicate,
                seeds=[7, 7],
                extra_copy_gaps=[1, 1],
                demo_count=3,
                query_count=4,
            )
        assert not duplicate.exists()


def test_writer_validates_pairwise_seed_setting_mapping():
    prototype = load_prototype()
    with TemporaryDirectory() as temporary:
        with pytest.raises(ValueError, match="same length"):
            prototype.write_evidence(
                Path(temporary) / "bad",
                seeds=[0, 1],
                extra_copy_gaps=[0],
                demo_count=3,
                query_count=4,
            )



def test_evidence_verifier_rejects_drift_in_every_source_binding():
    prototype = load_prototype()
    with TemporaryDirectory() as temporary:
        output = Path(temporary) / "source-bound-evidence"
        prototype.write_evidence(
            output,
            seeds=[10],
            extra_copy_gaps=[0],
            demo_count=3,
            query_count=1,
        )
        manifest_path = output / "manifest.json"
        original = manifest_path.read_bytes()
        cases = [
            ("prototype_source", "sha256", "prototype source hash mismatch"),
            ("generator_source", "sha256", "generator source hash mismatch"),
            ("canonical_rule", "sha256", "canonical rule hash mismatch"),
            ("canonical_rule", "catalog_hash", "canonical catalog hash mismatch"),
        ]
        for section, field, expected_error in cases:
            manifest = json.loads(original)
            manifest[section][field] = "0" * len(manifest[section][field])
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            verification = prototype.verify_evidence(output)
            assert verification["ok"] is False
            assert any(expected_error in error for error in verification["errors"])


def test_evidence_verifier_rejects_unsafe_paths_and_wrong_byte_counts():
    prototype = load_prototype()
    with TemporaryDirectory() as temporary:
        output = Path(temporary) / "path-bound-evidence"
        prototype.write_evidence(
            output,
            seeds=[10],
            extra_copy_gaps=[0],
            demo_count=3,
            query_count=1,
        )
        manifest_path = output / "manifest.json"
        original = manifest_path.read_bytes()

        escaped = output.parent / "escape.bin"
        escaped.write_bytes(b"outside evidence root")
        manifest = json.loads(original)
        manifest["files"][0] = {
            "path": "../escape.bin",
            "sha256": hashlib.sha256(escaped.read_bytes()).hexdigest(),
            "bytes": len(escaped.read_bytes()),
        }
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        traversal = prototype.verify_evidence(output)
        assert traversal["ok"] is False
        assert any("unsafe file path" in error for error in traversal["errors"])

        manifest = json.loads(original)
        manifest["files"][0]["bytes"] += 1
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        wrong_size = prototype.verify_evidence(output)
        assert wrong_size["ok"] is False
        assert any("byte count mismatch" in error for error in wrong_size["errors"])

def test_cli_writes_pairwise_settings_and_prints_machine_readable_summary(capsys):
    prototype = load_prototype()
    with TemporaryDirectory() as temporary:
        output = Path(temporary) / "cli-evidence"
        status = prototype.main(
            [
                "--seeds", "2", "3",
                "--extra-copy-gaps", "0", "1",
                "--demo-count", "3",
                "--query-count", "4",
                "--out", str(output),
            ]
        )
        assert status == 0
        summary = json.loads(capsys.readouterr().out)
        assert summary == {
            "demo_count": 3,
            "episodes": 2,
            "out": str(output),
            "query_count": 4,
            "racket_grid_executions": 36,
        }
        manifest = json.loads((output / "manifest.json").read_text())
        assert [row["extra_copy_gap"] for row in manifest["episodes"]] == [
            row["extra_copy_gap"] for row in sorted(
                manifest["episodes"], key=lambda row: row["public_challenge_id"]
            )
        ]
        assert {row["extra_copy_gap"] for row in manifest["episodes"]} == {0, 1}
