"""Focused contract tests for the nearest-corner tie-preference family."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes


TASK_ID = "89704f9047c0"
SETTINGS = (
    {"row_tie": "top", "column_tie": "left"},
    {"row_tie": "top", "column_tie": "right"},
    {"row_tie": "bottom", "column_tie": "left"},
    {"row_tie": "bottom", "column_tie": "right"},
)


def _root() -> Path:
    return find_root(__file__)


def _load(name: str):
    path = _root() / "generators" / TASK_ID / "workspace" / "parametric" / name
    assert path.is_file(), f"missing parametric implementation: {path}"
    spec = importlib.util.spec_from_file_location(f"_test_{TASK_ID}_{path.stem}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    rows = []
    with canonical_path(_root()).open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.append(row)
    assert len(rows) == 1
    return rows[0]["program_solution"]


def _inputs(episode: dict) -> list[list[list[int]]]:
    return [pair["input"] for pair in [*episode["train"], *episode["test"]]]


def test_default_program_is_exact_canonical_and_all_variants_are_distinct():
    prototype = _load("prototype.py")
    programs = [prototype.program(settings) for settings in SETTINGS]
    assert programs[0] == _canonical_program()
    assert len(set(programs)) == 4
    with pytest.raises(ValueError, match="exactly"):
        prototype.program({"row_tie": "top"})
    with pytest.raises(ValueError, match="row_tie"):
        prototype.program({"row_tie": "middle", "column_tie": "left"})


def test_python_rule_exposes_row_column_and_four_way_ties():
    prototype = _load("prototype.py")
    grid = [
        [1, 0, 0, 0, 2],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [3, 0, 0, 0, 4],
    ]
    expected = {
        ("top", "left"): (1, 1, 1),
        ("top", "right"): (1, 2, 2),
        ("bottom", "left"): (3, 1, 3),
        ("bottom", "right"): (3, 2, 4),
    }
    for settings in SETTINGS:
        output = prototype.apply_python(grid, settings)
        key = (settings["row_tie"], settings["column_tie"])
        assert (output[2][0], output[0][2], output[2][2]) == expected[key]


def test_two_demos_identify_every_setting_with_matched_inputs():
    prototype = _load("prototype.py")
    episodes = [prototype.generate_episode(44, settings, demos=2, queries=4) for settings in SETTINGS]
    baseline_inputs = _inputs(episodes[0])
    assert all(_inputs(episode) == baseline_inputs for episode in episodes[1:])
    assert [(len(pair["input"]), len(pair["input"][0])) for pair in episodes[0]["train"]] == [
        (5, 6),
        (6, 7),
    ]
    for settings, episode in zip(SETTINGS, episodes):
        assert prototype.teaching_survivors(episode) == [settings]


def test_query_prefixes_are_novel_distinct_large_and_reach_30_by_30():
    prototype = _load("prototype.py")
    one = prototype.generate_episode(91, SETTINGS[3], demos=3, queries=1)
    four = prototype.generate_episode(91, SETTINGS[3], demos=3, queries=4)
    assert one["train"] == four["train"]
    assert one["test"] == four["test"][:1]
    assert [(len(pair["input"]), len(pair["input"][0])) for pair in four["test"]] == [
        (29, 30),
        (30, 29),
        (29, 29),
        (30, 30),
    ]
    keys = {json.dumps(grid, separators=(",", ":")) for grid in _inputs(four)}
    assert len(keys) == len(_inputs(four))


def test_count_boundaries_determinism_and_setting_neutral_inputs():
    prototype = _load("prototype.py")
    for demos in (2, 6):
        for queries in (1, 8):
            first = prototype.generate_episode(1234, SETTINGS[0], demos=demos, queries=queries)
            second = prototype.generate_episode(1234, SETTINGS[0], demos=demos, queries=queries)
            alternate = prototype.generate_episode(1234, SETTINGS[2], demos=demos, queries=queries)
            assert first == second
            assert _inputs(first) == _inputs(alternate)
            assert len(first["train"]) == demos
            assert len(first["test"]) == queries
    for kwargs in ({"demos": 1, "queries": 4}, {"demos": 7, "queries": 4}, {"demos": 3, "queries": 0}, {"demos": 3, "queries": 9}):
        with pytest.raises(ValueError):
            prototype.generate_episode(0, SETTINGS[0], **kwargs)
    with pytest.raises(ValueError):
        prototype.generate_episode(True, SETTINGS[0], demos=3, queries=4)


def test_public_first_turn_is_prefix_stable_and_contains_no_private_fields():
    prototype = _load("prototype.py")
    one = prototype.generate_episode(777, SETTINGS[1], demos=3, queries=1)
    four = prototype.generate_episode(777, SETTINGS[1], demos=3, queries=4)
    visible_one = prototype.public_turn(one, 0)
    visible_four = prototype.public_turn(four, 0)
    assert public_challenge_bytes(visible_one) == public_challenge_bytes(visible_four)
    assert set(visible_four) == {"train", "test"}
    assert len(visible_four["test"]) == 1
    assert set(visible_four["test"][0]) == {"input"}
    raw = public_challenge_bytes(visible_four)
    assert prototype.public_turn_id(four, 0) == hashlib.sha256(raw).hexdigest()
    for forbidden in (b"row_tie", b"column_tie", b"program", b"query_count", b"answer"):
        assert forbidden not in raw
    with pytest.raises(IndexError):
        prototype.public_turn(one, 1)


def test_promotion_contract_declares_native_adapter_and_bounded_counts():
    contract_path = _root() / "generators" / TASK_ID / "workspace" / "parametric" / "promotion.json"
    assert contract_path.is_file(), f"missing promotion contract: {contract_path}"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"row_tie": ["top", "bottom"], "column_tie": ["left", "right"]},
        "default": {"row_tie": "top", "column_tie": "left"},
        "limits": {"demos": [2, 6], "queries": [1, 8]},
        "resources": [f"generators/{TASK_ID}/workspace/parametric/prototype.py"],
    }


def test_materializer_builds_native_jobs_and_reproducible_projection_evidence(tmp_path):
    materializer = _load("materialize_evidence.py")
    jobs = materializer.qualification_jobs(seed=20261024)
    assert len(jobs) == 4
    assert {json.dumps(job["settings"], sort_keys=True) for job in jobs} == {
        json.dumps(settings, sort_keys=True) for settings in SETTINGS
    }
    assert {(job["demos"], job["queries"]) for job in jobs} == {(3, 4)}

    result = materializer.materialize(
        tmp_path,
        root=_root(),
        seed=20261024,
        apply_program=materializer.python_apply_program,
    )
    execution = json.loads(Path(result["execution"]).read_text(encoding="utf-8"))
    adversarial = json.loads(Path(result["adversarial"]).read_text(encoding="utf-8"))
    assert len(result["public_files"]) == 4
    for public_name in result["public_files"]:
        public_path = Path(public_name)
        raw = public_path.read_bytes()
        assert public_path.name == f"challenge-{hashlib.sha256(raw).hexdigest()}.json"
        visible = json.loads(raw)
        assert set(visible) == {"train", "test"}
        assert len(visible["train"]) == 3
        assert len(visible["test"]) == 1
        assert set(visible["test"][0]) == {"input"}
    assert execution["racket"] == {"backend": "test", "protected": False}
    assert len(execution["checks"]) == 4
    assert all(len(check["survivors"]) == 1 for check in execution["checks"])
    assert adversarial["matched_inputs_across_settings"] is True
    assert adversarial["first_turn_matches_single_query"] is True
    assert adversarial["public_projection_private_fields_absent"] is True
    assert adversarial["ordinary_query_dimensions"] == [[29, 30], [30, 29], [29, 29], [30, 30]]
    assert adversarial["boundary_counts"] == {"minimum": {"demos": 2, "queries": 1}, "maximum": {"demos": 6, "queries": 8}}


def test_episode_errors_reports_malformed_demo_without_raising():
    prototype = _load("prototype.py")
    episode = copy.deepcopy(
        prototype.generate_episode(912, SETTINGS[0], demos=3, queries=4)
    )
    episode["train"][0]["input"][1][1] = 9

    errors = prototype.episode_errors(episode)

    assert any("train[0] invalid input" in error for error in errors)
