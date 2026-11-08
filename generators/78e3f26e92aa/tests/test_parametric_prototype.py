"""Focused tests for the task-local 78e3f26e92aa parametric prototype."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import load_selected_generator


HOME = Path(__file__).resolve().parents[1]
PROTOTYPE_PATH = HOME / "workspace" / "parametric" / "prototype.py"


def _load_prototype():
    spec = importlib.util.spec_from_file_location("parametric_78e3f26e92aa", PROTOTYPE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


proto = _load_prototype()
canonical, _, _ = load_selected_generator("78e3f26e92aa", root=HOME.parents[1])


def _input_key(grid):
    return json.dumps(grid, separators=(",", ":"))


def test_setting_contract_is_bounded_and_seed_selection_is_deterministic():
    assert proto.Setting(1, 6).as_dict() == {
        "step_multiplier": 1,
        "overlap_color": 6,
    }
    assert proto.Setting(2, 2) in proto.ALLOWED_SETTINGS
    assert proto.setting_for_seed(17) == proto.setting_for_seed(17)
    assert proto.setting_for_seed(17) in proto.ALLOWED_SETTINGS
    with pytest.raises(ValueError, match="step_multiplier"):
        proto.Setting(3, 6)
    with pytest.raises(ValueError, match="overlap_color"):
        proto.Setting(1, 9)
    with pytest.raises(TypeError, match="not bool"):
        proto.Setting(True, 6)


def test_canonical_setting_uses_exact_authority_and_python_mirror_matches_generator():
    setting = proto.Setting(1, 6)
    assert proto.racket_program(setting) == proto.canonical_program()
    for index in range(8):
        grid = canonical.generate(310, index, difficulty="hard")
        assert proto.python_mirror(grid, setting) == canonical.rule_mirror(grid)


def test_alternative_parameters_execute_real_rule_changes_on_witness_inputs():
    canonical_setting = proto.Setting(1, 6)
    alternatives = [proto.Setting(2, 6), proto.Setting(1, 2), proto.Setting(2, 2)]
    witnesses = [canonical.generate(911 + index, index, difficulty="hard") for index in range(48)]
    for alternative in alternatives:
        assert any(
            proto.python_mirror(grid, canonical_setting)
            != proto.python_mirror(grid, alternative)
            for grid in witnesses
        ), alternative


@pytest.mark.parametrize("setting", list(proto.ALLOWED_SETTINGS))
def test_episode_has_three_demos_four_distinct_queries_and_one_fixed_setting(setting):
    episode = proto.build_episode(
        seed=1701,
        setting=setting,
        demo_count=3,
        query_count=4,
        labeler=proto.python_labeler,
    )
    assert episode["setting"] == setting.as_dict()
    assert episode["demo_count"] == 3
    assert episode["query_count"] == 4
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 4
    all_inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
    assert len({_input_key(grid) for grid in all_inputs}) == 7
    assert all(pair["output"] == proto.python_mirror(pair["input"], setting)
               for pair in episode["train"] + episode["test"])


@pytest.mark.parametrize("setting", list(proto.ALLOWED_SETTINGS))
def test_demonstrations_alone_refute_every_other_setting_for_each_query(setting):
    episode = proto.build_episode(
        seed=2801,
        setting=setting,
        demo_count=3,
        query_count=4,
        labeler=proto.python_labeler,
    )
    assert episode["refuted_settings"] == [
        rival.as_dict() for rival in proto.ALLOWED_SETTINGS if rival != setting
    ]
    for query in episode["test"]:
        assert proto.lesson_ambiguities(episode["train"], query, setting) == []
        assert any(
            proto.python_mirror(query["input"], rival) != query["output"]
            for rival in proto.ALLOWED_SETTINGS
            if rival != setting
        )


@pytest.mark.parametrize(
    "kwargs,match",
    [
        ({"demo_count": 0}, "demo_count"),
        ({"query_count": 0}, "query_count"),
        ({"query_count": 5}, "query_count"),
        ({"demo_count": True}, "not bool"),
    ],
)
def test_invalid_episode_counts_fail_loudly(kwargs, match):
    with pytest.raises((TypeError, ValueError), match=match):
        proto.build_episode(seed=1, setting=proto.Setting(1, 6), **kwargs)


def test_public_projection_uses_only_visible_bytes_and_ignores_private_metadata():
    import copy

    episode = proto.build_episode(
        seed=3301,
        setting=proto.Setting(2, 2),
        labeler=proto.python_labeler,
    )
    baseline_bytes = proto.public_episode_bytes(episode)
    baseline_id = proto.public_episode_id(episode)

    hidden_mutation = copy.deepcopy(episode)
    hidden_mutation["seed"] = 999999
    hidden_mutation["setting"] = {"step_multiplier": 1, "overlap_color": 6}
    hidden_mutation["program"] = "private replacement"
    hidden_mutation["program_sha256"] = "0" * 64
    for pair in hidden_mutation["test"]:
        pair["output"] = [[9 for _ in row] for row in pair["output"]]

    assert proto.public_episode_bytes(hidden_mutation) == baseline_bytes
    assert proto.public_episode_id(hidden_mutation) == baseline_id
    public = json.loads(baseline_bytes)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert b'"setting"' not in baseline_bytes
    assert b'"seed"' not in baseline_bytes
    assert b'"program"' not in baseline_bytes


def test_write_batch_rejects_duplicate_visible_payload_before_writing(tmp_path):
    import copy

    episode = proto.build_episode(
        seed=4401,
        setting=proto.Setting(1, 6),
        labeler=proto.python_labeler,
    )
    duplicate = copy.deepcopy(episode)
    duplicate["seed"] += 1
    duplicate["setting"] = proto.Setting(2, 2).as_dict()
    with pytest.raises(ValueError, match="duplicate visible payload"):
        proto.write_batch([episode, duplicate], tmp_path)
    assert not (tmp_path / "manifest.json").exists()
    assert not (tmp_path / "public").exists()
    assert not (tmp_path / "private").exists()


def test_live_racket_labeler_matches_python_and_returns_bound_receipt():
    setting = proto.Setting(2, 2)
    grids = [canonical.generate(5501, index, difficulty="hard") for index in range(2)]
    execution = proto.execute_racket_labels(grids, setting)

    assert execution["outputs"] == [proto.python_mirror(grid, setting) for grid in grids]
    receipt = execution["receipt"]
    assert receipt["schema"] == "arcpuzzles-parametric-racket-receipt-v1"
    assert receipt["task_id"] == "78e3f26e92aa"
    assert receipt["setting"] == setting.as_dict()
    assert receipt["program"] == proto.racket_program(setting)
    assert receipt["program_sha256"] == proto.program_sha256(setting)
    assert receipt["runtime"]["backend"] == "racket"
    assert receipt["runtime"]["protected"] is True
    assert "ERROR" not in receipt["rule_response"]
    assert len(receipt["applications"]) == len(grids)
    for index, application in enumerate(receipt["applications"]):
        assert application["test_index"] == index
        assert application["command"] == f"(apply! {index})"
        assert "ERROR" not in application["response"]
        assert application["result_ref"].startswith("_")
        assert len(application["output_sha256"]) == 64


def test_racket_labeler_records_receipt_for_episode_construction():
    labeler = proto.RacketLabeler()
    episode = proto.build_episode(
        seed=6601,
        setting=proto.Setting(1, 2),
        labeler=labeler,
    )
    assert len(labeler.receipts) == 1
    assert labeler.receipts[0]["program_sha256"] == episode["program_sha256"]
    assert all(
        pair["output"] == proto.python_mirror(pair["input"], proto.Setting(1, 2))
        for pair in episode["train"] + episode["test"]
    )


def test_write_batch_emits_exact_public_bytes_and_private_evidence(tmp_path):
    episode = proto.build_episode(
        seed=7701,
        setting=proto.Setting(2, 6),
        labeler=proto.python_labeler,
    )
    receipt = {
        "schema": "arcpuzzles-parametric-racket-receipt-v1",
        "task_id": proto.TASK_ID,
        "setting": episode["setting"],
        "program_sha256": episode["program_sha256"],
        "runtime": {"backend": "racket", "protected": True},
        "applications": [],
    }
    manifest = proto.write_batch([episode], tmp_path, receipts=[receipt])
    public_id = proto.public_episode_id(episode)
    public_path = tmp_path / "public" / f"{public_id}.json"
    private_path = tmp_path / "private" / f"{public_id}.private.json"

    assert public_path.read_bytes() == proto.public_episode_bytes(episode)
    private = json.loads(private_path.read_text(encoding="utf-8"))
    assert private["public_id"] == public_id
    assert private["episode"]["setting"] == episode["setting"]
    assert all("output" in pair for pair in private["episode"]["test"])
    assert private["racket_receipt"] == receipt
    assert manifest == json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["episode_count"] == 1
    assert manifest["episodes"][0]["public_id"] == public_id
    assert manifest["episodes"][0]["public_path"] == f"public/{public_id}.json"
    assert manifest["episodes"][0]["private_path"] == f"private/{public_id}.private.json"


def test_cli_build_writes_one_racket_backed_episode_and_readme_documents_command(tmp_path, capsys):
    output_dir = tmp_path / "run"
    result = proto.main(
        [
            "build",
            "--seed",
            "8801",
            "--setting",
            "canonical",
            "--demo-count",
            "3",
            "--query-count",
            "4",
            "--out",
            str(output_dir),
        ]
    )
    assert result == 0
    summary = json.loads(capsys.readouterr().out)
    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    assert summary["manifest"] == str(output_dir / "manifest.json")
    assert summary["episode_count"] == 1
    assert manifest["episode_count"] == 1
    public_files = list((output_dir / "public").glob("*.json"))
    private_files = list((output_dir / "private").glob("*.private.json"))
    assert len(public_files) == 1
    assert len(private_files) == 1
    private = json.loads(private_files[0].read_text(encoding="utf-8"))
    assert private["racket_receipt"]["runtime"]["protected"] is True
    readme = (HOME / "workspace" / "parametric" / "README.md").read_text(encoding="utf-8")
    assert "python3 run_with_racket.py python3 generators/78e3f26e92aa/workspace/parametric/prototype.py build" in readme
    assert "--demo-count 3" in readme
    assert "--query-count 4" in readme


def _offline_receipt_for_episode(episode):
    import hashlib

    def output_sha(grid):
        body = (json.dumps(grid, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
        return hashlib.sha256(body).hexdigest()

    pairs = episode["train"] + episode["test"]
    return {
        "schema": "arcpuzzles-parametric-racket-receipt-v1",
        "task_id": proto.TASK_ID,
        "setting": episode["setting"],
        "program": episode["program"],
        "program_sha256": episode["program_sha256"],
        "runtime": {"backend": "racket", "protected": True},
        "rule_response": "&1 = rule set. Use (test! N) to verify.",
        "applications": [
            {
                "test_index": index,
                "command": f"(apply! {index})",
                "response": f"_{index + 1} = Grid(1x1) — applied rule",
                "result_ref": f"_{index + 1}",
                "output_sha256": output_sha(pair["output"]),
            }
            for index, pair in enumerate(pairs)
        ],
    }


def test_verify_batch_rechecks_projection_parity_identifiability_and_receipts(tmp_path):
    episode = proto.build_episode(seed=9901, labeler=proto.python_labeler)
    receipt = _offline_receipt_for_episode(episode)
    proto.write_batch([episode], tmp_path, receipts=[receipt])

    report = proto.verify_batch(tmp_path)
    assert report["status"] == "pass"
    assert report["task_id"] == proto.TASK_ID
    assert report["episode_count"] == 1
    assert report["public_ids"] == [proto.public_episode_id(episode)]
    assert report["settings"] == [episode["setting"]]
    assert report["checks"]["public_projection"] == "pass"
    assert report["checks"]["python_parity"] == "pass"
    assert report["checks"]["demo_identifiability"] == "pass"
    assert report["checks"]["protected_racket_receipts"] == "pass"


def test_verify_batch_rejects_tampered_public_bytes(tmp_path):
    episode = proto.build_episode(seed=10002, labeler=proto.python_labeler)
    receipt = _offline_receipt_for_episode(episode)
    proto.write_batch([episode], tmp_path, receipts=[receipt])
    public_path = next((tmp_path / "public").glob("*.json"))
    public = json.loads(public_path.read_text(encoding="utf-8"))
    public["test"][0]["input"][0][0] = (public["test"][0]["input"][0][0] + 1) % 10
    public_path.write_text(
        json.dumps(public, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="public (content ID|bytes)"):
        proto.verify_batch(tmp_path)


def test_cli_verify_writes_machine_readable_report(tmp_path, capsys):
    export_dir = tmp_path / "export"
    report_path = tmp_path / "verification.json"
    episode = proto.build_episode(seed=11003, labeler=proto.python_labeler)
    proto.write_batch(
        [episode],
        export_dir,
        receipts=[_offline_receipt_for_episode(episode)],
    )

    result = proto.main(
        ["verify", "--input", str(export_dir), "--report", str(report_path)]
    )
    assert result == 0
    printed = json.loads(capsys.readouterr().out)
    written = json.loads(report_path.read_text(encoding="utf-8"))
    assert printed == written
    assert written["status"] == "pass"


def test_write_batch_sorts_manifest_entries_by_public_id(tmp_path):
    episodes = [
        proto.build_episode(seed=12000, labeler=proto.python_labeler),
        proto.build_episode(seed=12001, labeler=proto.python_labeler),
    ]
    receipts = [_offline_receipt_for_episode(episode) for episode in episodes]
    paired = list(zip(episodes, receipts))
    paired.sort(key=lambda item: proto.public_episode_id(item[0]), reverse=True)

    manifest = proto.write_batch(
        [episode for episode, _ in paired],
        tmp_path,
        receipts=[receipt for _, receipt in paired],
    )
    public_ids = [entry["public_id"] for entry in manifest["episodes"]]
    assert public_ids == sorted(public_ids)


def test_verify_batch_rejects_unsorted_manifest_entries(tmp_path):
    episodes = [
        proto.build_episode(seed=13000, labeler=proto.python_labeler),
        proto.build_episode(seed=13001, labeler=proto.python_labeler),
    ]
    proto.write_batch(
        episodes,
        tmp_path,
        receipts=[_offline_receipt_for_episode(episode) for episode in episodes],
    )
    manifest_path = tmp_path / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["episodes"] = list(reversed(manifest["episodes"]))
    manifest_path.write_text(
        json.dumps(manifest, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="sorted by public_id"):
        proto.verify_batch(tmp_path)
