from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


PROTOTYPE_PATH = Path(__file__).resolve().parents[1] / "workspace" / "parametric" / "prototype.py"
SPEC = importlib.util.spec_from_file_location("parametric_branch_mode_1856980929fe", PROTOTYPE_PATH)
assert SPEC and SPEC.loader
prototype = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = prototype
SPEC.loader.exec_module(prototype)


def _canonical_pairs():
    ledger = Path(__file__).resolve().parents[3] / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in ledger.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == "1856980929fe":
            test = row["test"] if isinstance(row["test"], list) else [row["test"]]
            return [*row["train"], *test]
    raise AssertionError("canonical task not found")


def test_branch_mode_python_outputs_are_literal_and_directional():
    grid = [
        [0, 0, 0, 3, 3, 0, 0, 0, 0],
        [0, 0, 0, 3, 3, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]
    left = [
        [0, 0, 0, 3, 3, 0, 0, 0, 0],
        [0, 0, 0, 3, 3, 0, 0, 0, 0],
        [0, 3, 3, 0, 0, 0, 0, 0, 0],
        [0, 3, 3, 0, 0, 0, 0, 0, 0],
        [3, 0, 0, 0, 0, 0, 0, 0, 0],
        [3, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]
    right = [
        [0, 0, 0, 3, 3, 0, 0, 0, 0],
        [0, 0, 0, 3, 3, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 3, 3, 0, 0],
        [0, 0, 0, 0, 0, 3, 3, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 3, 3],
        [0, 0, 0, 0, 0, 0, 0, 3, 3],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]
    both = [[max(a, b) for a, b in zip(lrow, rrow)] for lrow, rrow in zip(left, right)]

    assert prototype.apply_python(grid, "left") == left
    assert prototype.apply_python(grid, "right") == right
    assert prototype.apply_python(grid, "both") == both


def test_canonical_default_is_exact_rule_and_matches_all_canonical_pairs():
    assert prototype.PARAMETER_SPEC == {
        "name": "branch_mode",
        "values": ("both", "left", "right"),
        "default": "both",
    }
    assert prototype.materialize_rule("both") == prototype.canonical_rule()
    for pair in _canonical_pairs():
        assert prototype.apply_python(pair["input"], "both") == pair["output"]


def _input_hashes(episode):
    return [
        prototype.grid_sha256(pair["input"])
        for pair in [*episode["train"], *episode["test"]]
    ]


def test_episode_holds_one_mode_and_has_five_demos_four_distinct_queries():
    for seed, mode in ((30, "both"), (31, "left"), (32, "right")):
        episode = prototype.build_episode(
            seed=seed,
            branch_mode=mode,
            difficulty="medium",
            n_train=5,
            n_test=4,
        )
        assert len(episode["train"]) == 5
        assert len(episode["test"]) == 4
        assert episode["meta"]["parameters"] == {"branch_mode": mode}
        assert episode["meta"]["parameter_scope"] == "chosen once per episode"
        hashes = _input_hashes(episode)
        assert len(hashes) == len(set(hashes)) == 9
        for pair in [*episode["train"], *episode["test"]]:
            outputs = {
                candidate: prototype.apply_python(pair["input"], candidate)
                for candidate in prototype.PARAMETER_SPEC["values"]
            }
            assert len({prototype.grid_sha256(value) for value in outputs.values()}) == 3
            assert pair["output"] == outputs[mode]
        assert prototype.parameter_rival_findings(episode) == []
        query_rows = prototype.query_identifiability(episode)
        assert len(query_rows) == 4
        assert all(row["identifiable_from_demonstrations"] for row in query_rows)
        assert all(row["all_rivals_change_query"] for row in query_rows)


def test_setting_selection_counts_and_sampler_limits_fail_loudly():
    assert [prototype.choose_branch_mode(seed) for seed in range(6)] == [
        "both",
        "left",
        "right",
        "both",
        "left",
        "right",
    ]
    with pytest.raises(TypeError, match="seed"):
        prototype.choose_branch_mode(True)
    with pytest.raises(ValueError, match="n_train"):
        prototype.build_episode(seed=0, n_train=0, n_test=4)
    with pytest.raises(ValueError, match="n_test"):
        prototype.build_episode(seed=0, n_train=5, n_test=0)
    with pytest.raises(RuntimeError, match="exhausted"):
        prototype.build_episode(seed=0, n_train=5, n_test=4, max_attempts=1)


def test_public_projection_and_identifier_use_visible_bytes_only():
    from copy import deepcopy

    episode = prototype.build_episode(
        seed=31,
        branch_mode="left",
        n_train=5,
        n_test=4,
    )
    public = prototype.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])

    baseline_id = prototype.public_id(episode)
    hidden_changed = deepcopy(episode)
    hidden_changed["meta"]["seed"] = 999999
    hidden_changed["meta"]["parameters"]["branch_mode"] = "right"
    hidden_changed["test"][0]["output"][0][0] = 9
    assert prototype.public_id(hidden_changed) == baseline_id

    visible_changed = deepcopy(episode)
    visible_changed["test"][0]["input"][0][0] = 9
    assert prototype.public_id(visible_changed) != baseline_id


def test_materialized_racket_rules_match_python_and_canonical_labels():
    episode = prototype.build_episode(
        seed=30,
        branch_mode="both",
        n_train=1,
        n_test=1,
    )
    representative = episode["train"][0]["input"]
    for mode in prototype.PARAMETER_SPEC["values"]:
        assert prototype.apply_racket(representative, mode) == prototype.apply_python(
            representative, mode
        )
    for pair in _canonical_pairs():
        assert prototype.apply_racket(pair["input"], "both") == pair["output"]


def test_evidence_writer_executes_racket_and_content_addresses_public_files(tmp_path):
    evidence = prototype.build_evidence(
        seeds=[30, 31, 32],
        difficulty="medium",
        n_train=1,
        n_test=1,
    )
    assert evidence["summary"] == {
        "episodes": 3,
        "racket_labeled_pairs": 6,
        "canonical_checks": 4,
        "canonical_passed": 4,
        "python_parity_passed": 6,
        "identifiable_queries": 3,
        "total_queries": 3,
    }
    prototype.write_evidence(tmp_path, evidence)

    manifest_path = tmp_path / "private" / "manifest.json"
    assert manifest_path.is_file()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["summary"] == evidence["summary"]
    assert set(manifest["programs"]) == {"both", "left", "right"}

    public_files = sorted((tmp_path / "public").glob("challenge_*.json"))
    private_files = sorted((tmp_path / "private" / "episodes").glob("*.json"))
    assert len(public_files) == len(private_files) == 3
    for row in evidence["episodes"]:
        public_path = tmp_path / "public" / f"challenge_{row['public_id']}.json"
        private_path = tmp_path / "private" / "episodes" / f"{row['public_id']}.json"
        assert public_path.read_bytes() == prototype.public_bytes(row["episode"])
        public_text = public_path.read_text(encoding="utf-8")
        assert "branch_mode" not in public_text
        assert '"seed"' not in public_text
        private = json.loads(private_path.read_text(encoding="utf-8"))
        assert private["meta"]["parameters"] == row["episode"]["meta"]["parameters"]
        assert all("output" in pair for pair in private["test"])

    duplicated = dict(evidence)
    duplicated["episodes"] = [*evidence["episodes"], evidence["episodes"][0]]
    with pytest.raises(ValueError, match="duplicate public challenge"):
        prototype.write_evidence(tmp_path / "duplicate", duplicated)



def _lightweight_writer_evidence():
    programs = {}
    for mode in prototype.PARAMETER_SPEC["values"]:
        source = prototype.materialize_rule(mode)
        programs[mode] = {
            "source": source,
            "sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
            "bytes": len(source.encode("utf-8")),
            "canonical_default": mode == prototype.PARAMETER_SPEC["default"],
        }
    rows = []
    for seed in (30, 31, 32):
        mode = prototype.choose_branch_mode(seed)
        episode = prototype.build_episode(
            seed=seed,
            branch_mode=mode,
            n_train=1,
            n_test=1,
        )
        rows.append(
            {
                "public_id": prototype.public_id(episode),
                "seed": seed,
                "branch_mode": mode,
                "program_sha256": programs[mode]["sha256"],
                "episode": episode,
                "rival_findings": [],
                "query_identifiability": prototype.query_identifiability(episode),
                "racket_python_checks": [],
            }
        )
    return {
        "schema": "1856980929fe-branch-mode-evidence-v1",
        "task_id": prototype.TASK_ID,
        "parameter_spec": {
            "name": "branch_mode",
            "values": ["both", "left", "right"],
            "default": "both",
            "scope": "chosen once per episode",
        },
        "generator": {
            "version": prototype._GEN.VERSION,
            "rule_hash": prototype._GEN.RULE_HASH,
            "sha256": prototype.generator_sha256(),
        },
        "prototype": {
            "path": "workspace/parametric/prototype.py",
            "sha256": hashlib.sha256(PROTOTYPE_PATH.read_bytes()).hexdigest(),
        },
        "programs": programs,
        "canonical_checks": [],
        "episodes": rows,
        "summary": {"episodes": len(rows)},
        "limitations": ["test fixture"],
    }


def test_evidence_writer_sorts_batch_by_visible_public_identifier(tmp_path):
    evidence = _lightweight_writer_evidence()
    evidence["episodes"] = sorted(
        evidence["episodes"], key=lambda row: row["public_id"], reverse=True
    )
    manifest = prototype.write_evidence(tmp_path, evidence)
    written_ids = [row["public_id"] for row in manifest["episodes"]]
    assert written_ids == sorted(written_ids)


def test_evidence_verifier_detects_public_payload_tampering(tmp_path):
    evidence = _lightweight_writer_evidence()
    prototype.write_evidence(tmp_path, evidence)
    report = prototype.verify_evidence(tmp_path)
    assert report == {
        "programs": 3,
        "episodes": 3,
        "public_files": 3,
        "private_labeled_pairs": 6,
        "racket_rechecks": 0,
    }

    public_path = next((tmp_path / "public").glob("challenge_*.json"))
    public_path.write_bytes(public_path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="public bytes mismatch"):
        prototype.verify_evidence(tmp_path)




@pytest.mark.parametrize("bad_cell", [True, 1.5, "0) (error 'unsafe) ("])
def test_racket_grid_literal_rejects_non_integer_arc_cells(bad_cell):
    """Catch raw or bool cell values being interpolated into executable Racket."""
    with pytest.raises(ValueError, match="integer ARC colors"):
        prototype._grid_literal([[bad_cell]])


def test_evidence_builder_requires_default_and_alternative_settings():
    """A retained parameter demonstration cannot contain only one setting class."""
    with pytest.raises(ValueError, match="canonical default.*alternative"):
        prototype.build_evidence(seeds=[31], n_train=1, n_test=1)



def test_evidence_writer_validates_programs_before_creating_destination(tmp_path):
    """A validation failure must not poison the immutable output path."""
    evidence = _lightweight_writer_evidence()
    evidence["programs"]["left"]["sha256"] = "0" * 64
    destination = tmp_path / "evidence"
    with pytest.raises(ValueError, match="program hash mismatch"):
        prototype.write_evidence(destination, evidence)
    assert not destination.exists()

def test_evidence_writer_rejects_symlink_destination(tmp_path):
    """Writing evidence must not follow an output-directory symlink."""
    target = tmp_path / "target"
    target.mkdir()
    destination = tmp_path / "evidence-link"
    destination.symlink_to(target, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        prototype.write_evidence(destination, _lightweight_writer_evidence())



def test_evidence_writer_retains_prototype_source_binding(tmp_path):
    """The retained manifest must name and hash the prototype that authored it."""
    evidence = _lightweight_writer_evidence()
    manifest = prototype.write_evidence(tmp_path, evidence)
    assert manifest["prototype"] == evidence["prototype"]


def test_evidence_verifier_rejects_stale_prototype_binding(tmp_path):
    """Changing the prototype implementation must invalidate retained evidence."""
    prototype.write_evidence(tmp_path, _lightweight_writer_evidence())
    manifest_path = tmp_path / "private" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.setdefault("prototype", {})["sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="prototype source mismatch"):
        prototype.verify_evidence(tmp_path)

def test_evidence_verifier_rejects_stale_manifest_generator_binding(tmp_path):
    """Changing generator.py must invalidate a retained manifest."""
    prototype.write_evidence(tmp_path, _lightweight_writer_evidence())
    manifest_path = tmp_path / "private" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["generator"]["sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="generator source mismatch"):
        prototype.verify_evidence(tmp_path)


def test_evidence_verifier_rejects_stale_episode_generator_binding(tmp_path):
    """Hidden episode metadata must remain bound to the current generator source."""
    prototype.write_evidence(tmp_path, _lightweight_writer_evidence())
    episode_path = next((tmp_path / "private" / "episodes").glob("*.json"))
    episode = json.loads(episode_path.read_text(encoding="utf-8"))
    episode["meta"]["generator_sha256"] = "0" * 64
    episode_path.write_text(json.dumps(episode), encoding="utf-8")
    with pytest.raises(ValueError, match="episode generator source mismatch"):
        prototype.verify_evidence(tmp_path)


@pytest.mark.parametrize(
    ("relative_path", "message"),
    [
        ("private/episodes/stale.json", "private episode file set mismatch"),
        ("private/rules/stale.rkt", "private rule file set mismatch"),
    ],
)
def test_evidence_verifier_rejects_unmanifested_private_files(
    tmp_path, relative_path, message
):
    """A verifier must reject stale answers or programs mixed into a bundle."""
    prototype.write_evidence(tmp_path, _lightweight_writer_evidence())
    stale_path = tmp_path / relative_path
    stale_path.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        prototype.verify_evidence(tmp_path)

def test_cli_build_and_verify_round_trip(tmp_path):
    output_dir = tmp_path / "evidence"
    build = subprocess.run(
        [
            sys.executable,
            str(PROTOTYPE_PATH),
            "build",
            "--seeds",
            "30",
            "31",
            "32",
            "--difficulty",
            "medium",
            "--demos",
            "1",
            "--queries",
            "1",
            "--out",
            str(output_dir),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert build.returncode == 0, build.stderr
    build_report = json.loads(build.stdout)
    assert build_report["summary"]["episodes"] == 3
    assert build_report["output"] == str(output_dir.resolve())

    verify = subprocess.run(
        [
            sys.executable,
            str(PROTOTYPE_PATH),
            "verify",
            "--out",
            str(output_dir),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert verify.returncode == 0, verify.stderr
    assert json.loads(verify.stdout) == {
        "episodes": 3,
        "private_labeled_pairs": 6,
        "programs": 3,
        "public_files": 3,
        "racket_rechecks": 0,
    }
