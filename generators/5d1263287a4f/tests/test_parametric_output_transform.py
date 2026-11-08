"""Focused tests for the proposed output-transform episode prototype."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "5d1263287a4f"
ROOT = find_root(__file__)
PROTOTYPE_PATH = (
    Path(__file__).resolve().parents[1]
    / "workspace"
    / "parametric"
    / "prototype.py"
)


def _load_prototype():
    spec = importlib.util.spec_from_file_location(
        "prototype_5d1263287a4f_output_transform", PROTOTYPE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import prototype from {PROTOTYPE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PROTOTYPE = _load_prototype()


def _canonical_program() -> str:
    programs = {
        row["program_solution"]
        for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines()
        if (row := json.loads(line)).get("task_id") == TASK_ID
    }
    assert len(programs) == 1
    return next(iter(programs))


def _hand_input() -> list[list[int]]:
    # A|A|A with an asymmetric three-color A.
    return [
        [0, 1, 0, 1, 0, 1],
        [2, 0, 2, 0, 2, 0],
    ]


def _grid_key(grid) -> str:
    return json.dumps(grid, separators=(",", ":"))


def test_parameter_declaration_and_canonical_program_are_exact():
    canonical = _canonical_program()
    assert PROTOTYPE.PARAMETER_NAME == "output_transform"
    assert PROTOTYPE.ALLOWED_SETTINGS == (
        "identity",
        "horizontal_mirror",
        "vertical_flip",
    )
    assert PROTOTYPE.DEFAULT_SETTING == "identity"
    assert PROTOTYPE.canonical_program() == canonical
    assert PROTOTYPE.program_for("identity") == canonical
    assert PROTOTYPE.rule_callable(canonical) == wrap_rule(canonical)

    replacements = {
        "horizontal_mirror": "(at g r (- pw 1 c))",
        "vertical_flip": "(at g (- h 1 r) c)",
    }
    for setting, expression in replacements.items():
        variant = PROTOTYPE.program_for(setting)
        assert variant != canonical
        assert variant.count(expression) == 1
        assert variant.replace(expression, "(at g r c)") == canonical


def test_python_mirror_has_hand_checked_outputs_for_all_settings():
    grid = _hand_input()
    expected = {
        "identity": [[0, 1], [2, 0]],
        "horizontal_mirror": [[1, 0], [0, 2]],
        "vertical_flip": [[2, 0], [0, 1]],
    }
    before = copy.deepcopy(grid)
    for setting, output in expected.items():
        assert PROTOTYPE.apply_python(grid, setting) == output
    assert grid == before
    assert len({_grid_key(value) for value in expected.values()}) == 3


def test_setting_is_deterministic_and_episode_fixed_with_four_distinct_queries():
    assert PROTOTYPE.choose_setting(12345) == PROTOTYPE.choose_setting(12345)
    assert {
        PROTOTYPE.choose_setting(seed) for seed in range(128)
    } == set(PROTOTYPE.ALLOWED_SETTINGS)

    episode = PROTOTYPE.build_episode(
        20261023,
        setting="horizontal_mirror",
        demo_count=5,
        query_count=4,
    )
    assert episode["meta"][PROTOTYPE.PARAMETER_NAME] == "horizontal_mirror"
    assert episode["meta"]["demo_count"] == 5
    assert episode["meta"]["query_count"] == 4
    assert len(episode["train"]) == 5
    assert len(episode["test"]) == 4

    pairs = episode["train"] + episode["test"]
    assert len({_grid_key(pair["input"]) for pair in pairs}) == 9
    for pair in pairs:
        outputs = {
            setting: PROTOTYPE.apply_python(pair["input"], setting)
            for setting in PROTOTYPE.ALLOWED_SETTINGS
        }
        assert len({_grid_key(value) for value in outputs.values()}) == 3
        assert pair["output"] == outputs["horizontal_mirror"]

    for rival in {"identity", "vertical_flip"}:
        assert any(
            PROTOTYPE.apply_python(pair["input"], rival) != pair["output"]
            for pair in episode["train"]
        )


def test_demo_and_query_counts_are_independent():
    first = PROTOTYPE.build_episode(
        91, setting="identity", demo_count=2, query_count=6
    )
    second = PROTOTYPE.build_episode(
        91, setting="vertical_flip", demo_count=6, query_count=2
    )
    assert (len(first["train"]), len(first["test"])) == (2, 6)
    assert (len(second["train"]), len(second["test"])) == (6, 2)


@pytest.mark.parametrize("seed", [True, -1, 1.5, "1"])
def test_invalid_seed_fails_loudly(seed):
    with pytest.raises((TypeError, ValueError)):
        PROTOTYPE.choose_setting(seed)
    with pytest.raises((TypeError, ValueError)):
        PROTOTYPE.build_episode(seed)


@pytest.mark.parametrize("setting", [None, "rotate_90", 1])
def test_invalid_setting_fails_loudly(setting):
    with pytest.raises((TypeError, ValueError)):
        PROTOTYPE.program_for(setting)
    with pytest.raises((TypeError, ValueError)):
        PROTOTYPE.build_episode(1, setting=setting)


@pytest.mark.parametrize(
    "field,value",
    [
        ("demo_count", 0),
        ("demo_count", 33),
        ("demo_count", True),
        ("query_count", 0),
        ("query_count", 33),
        ("query_count", False),
    ],
)
def test_invalid_counts_fail_loudly(field, value):
    kwargs = {"demo_count": 4, "query_count": 4, field: value}
    with pytest.raises((TypeError, ValueError)):
        PROTOTYPE.build_episode(1, **kwargs)


def test_public_projection_redacts_private_fields_and_name_uses_visible_bytes_only():
    episode = PROTOTYPE.build_episode(
        42, setting="vertical_flip", demo_count=4, query_count=4
    )
    public = PROTOTYPE.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert public_challenge_bytes(public) == public_challenge_bytes(episode)

    expected_name = f"challenge-{public_challenge_id(public)}.json"
    assert PROTOTYPE.public_filename(episode) == expected_name

    private_only = copy.deepcopy(episode)
    private_only["meta"]["seed"] += 1
    private_only["meta"][PROTOTYPE.PARAMETER_NAME] = "identity"
    private_only["program"] = "private program changed"
    private_only["test"][0]["output"][0][0] = (
        private_only["test"][0]["output"][0][0] + 1
    ) % 10
    assert PROTOTYPE.public_filename(private_only) == expected_name

    visible_change = copy.deepcopy(episode)
    visible_change["train"][0]["output"][0][0] = (
        visible_change["train"][0]["output"][0][0] + 1
    ) % 10
    assert PROTOTYPE.public_filename(visible_change) != expected_name

    public["train"][0]["input"][0][0] = (public["train"][0]["input"][0][0] + 1) % 10
    assert public["train"][0]["input"] != episode["train"][0]["input"]


def _load_verify():
    verify_path = PROTOTYPE_PATH.with_name("verify.py")
    spec = importlib.util.spec_from_file_location(
        "verify_5d1263287a4f_output_transform", verify_path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import verifier from {verify_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_racket_executes_all_three_programs_exactly_on_same_input():
    from arc_repl.racket_bridge import RacketBridge

    verify = _load_verify()
    grid = _hand_input()
    bridge = RacketBridge(timeout=30, max_calls_before_restart=64)
    try:
        actual = {
            setting: verify.execute_program(
                bridge, PROTOTYPE.program_for(setting), grid
            )
            for setting in PROTOTYPE.ALLOWED_SETTINGS
        }
    finally:
        bridge.shutdown()

    assert actual == {
        setting: PROTOTYPE.apply_python(grid, setting)
        for setting in PROTOTYPE.ALLOWED_SETTINGS
    }
    assert len({_grid_key(output) for output in actual.values()}) == 3


def test_evidence_writer_retains_exact_public_bytes_and_manifest(tmp_path):
    import hashlib

    verify = _load_verify()
    out_dir = tmp_path / "evidence"
    report = verify.build_evidence(
        out_dir=out_dir,
        start_seed=100,
        demo_count=2,
        query_count=4,
    )
    assert report["status"] == "passed"
    assert report["counts"] == {
        "settings": 3,
        "episodes": 3,
        "demonstrations_per_episode": 2,
        "queries_per_episode": 4,
        "racket_program_applications": 54,
    }
    assert report["all_racket_exact"] is True
    assert report["all_inputs_pairwise_setting_sensitive"] is True
    assert report["all_demos_identify_setting"] is True
    assert report["all_queries_setting_sensitive"] is True
    assert set(report["settings"]) == set(PROTOTYPE.ALLOWED_SETTINGS)
    public_batch = report["public_batch"]
    assert [row["public_id"] for row in public_batch] == sorted(
        row["public_id"] for row in public_batch
    )
    assert [row["filename"] for row in public_batch] == [
        f"challenge-{row['public_id']}.json" for row in public_batch
    ]

    manifest = json.loads((out_dir / "manifest.json").read_text())
    for relative, record in manifest["files"].items():
        data = (out_dir / relative).read_bytes()
        assert hashlib.sha256(data).hexdigest() == record["sha256"]
        assert len(data) == record["bytes"]

    public_names = []
    for setting, row in report["settings"].items():
        private_path = out_dir / row["private_episode"]
        public_path = out_dir / row["public_challenge"]
        episode = json.loads(private_path.read_text())
        assert public_path.read_bytes() == public_challenge_bytes(episode)
        assert public_path.name == PROTOTYPE.public_filename(episode)
        assert setting not in public_path.name
        assert str(row["seed"]) not in public_path.name
        public_names.append(public_path.name)
        assert len(episode["test"]) == 4
        assert all("output" in pair for pair in episode["test"])
        visible = json.loads(public_path.read_text())
        assert all("output" not in pair for pair in visible["test"])

    assert len(set(public_names)) == 3
    disagreement = json.loads(
        (out_dir / "private" / "same-input-disagreement.json").read_text()
    )
    assert set(disagreement["outputs"]) == set(PROTOTYPE.ALLOWED_SETTINGS)
    assert len({_grid_key(value) for value in disagreement["outputs"].values()}) == 3

    with pytest.raises(FileExistsError):
        verify.build_evidence(
            out_dir=out_dir,
            start_seed=100,
            demo_count=2,
            query_count=4,
        )


def test_public_batch_exports_are_sorted_by_id_and_reject_duplicates():
    verify = _load_verify()
    episodes = {
        setting: PROTOTYPE.build_episode(
            500 + index,
            setting=setting,
            demo_count=2,
            query_count=4,
        )
        for index, setting in enumerate(reversed(PROTOTYPE.ALLOWED_SETTINGS))
    }

    exports = verify.prepare_public_exports(episodes)
    public_ids = [row["public_id"] for row in exports]
    assert public_ids == sorted(public_ids)
    assert [row["filename"] for row in exports] == [
        f"challenge-{public_id}.json" for public_id in public_ids
    ]
    assert len({row["visible_bytes"] for row in exports}) == len(exports)

    duplicate = copy.deepcopy(next(iter(episodes.values())))
    with pytest.raises(ValueError, match="duplicate visible payload"):
        verify.prepare_public_exports({"first": duplicate, "second": duplicate})


def test_verifier_bootstraps_rule_parser_in_source_and_staged_layouts(monkeypatch):
    import sys

    verify = _load_verify()
    monkeypatch.delitem(sys.modules, "scripts.comment_solutions", raising=False)
    monkeypatch.delitem(sys.modules, "scripts", raising=False)
    verify._install_packet_scripts_namespace(ROOT)
    assert "scripts.comment_solutions" in sys.modules
    assert PROTOTYPE.rule_callable(PROTOTYPE.canonical_program()).startswith("(lambda")
