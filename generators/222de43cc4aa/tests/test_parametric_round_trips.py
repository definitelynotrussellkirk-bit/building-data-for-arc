"""Focused tests for the proposed round-trip-count prototype."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes

TASK_ID = "222de43cc4aa"
ROOT = find_root(__file__)
PROTOTYPE_PATH = ROOT / "generators" / TASK_ID / "workspace/parametric/prototype.py"


def load_prototype():
    spec = importlib.util.spec_from_file_location(
        f"round_trip_prototype_{TASK_ID}", PROTOTYPE_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def canonical_program() -> str:
    rows = []
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and row.get("content_hash") == TASK_ID:
                rows.append(row)
    assert len(rows) == 1
    return rows[0]["program_solution"].strip()


def test_default_rule_is_exact_canonical_and_alternate_changes_only_trip_count():
    proto = load_prototype()
    canonical = canonical_program()
    assert proto.DEFAULT_ROUND_TRIPS == 2
    assert proto.ALLOWED_ROUND_TRIPS == (1, 2)
    assert proto.rule_source(2) == canonical
    alternate = proto.rule_source(1)
    assert alternate != canonical
    assert "(* 2 period)" in alternate
    assert "(* 4 period)" not in alternate


@pytest.mark.parametrize("value", [0, 3, -1, True, 1.0, "2", None])
def test_round_trip_setting_rejects_out_of_contract_values(value):
    proto = load_prototype()
    with pytest.raises(ValueError, match="round_trips"):
        proto.rule_source(value)


def test_python_mirror_has_hand_derived_pingpong_rows_for_both_settings():
    proto = load_prototype()
    grid = [[1], [2], [3]]
    assert proto.python_mirror(grid, 1) == [[1], [2], [3], [2], [1]]
    assert proto.python_mirror(grid, 2) == [
        [1], [2], [3], [2], [1], [2], [3], [2], [1]
    ]

    taller = [[0], [1], [2], [3]]
    assert proto.python_mirror(taller, 1) == [
        [0], [1], [2], [3], [2], [1], [0]
    ]


@pytest.mark.parametrize(
    "grid",
    [[], [[]], [[1], [2, 3]], [[True]], [[10]], [[1]]],
)
def test_python_mirror_rejects_malformed_or_too_short_grids(grid):
    proto = load_prototype()
    with pytest.raises(ValueError, match="grid"):
        proto.python_mirror(grid, 1)


def _controlled_executor(proto, calls):
    canonical = canonical_program()

    def execute(source, grids):
        trips = 2 if source == canonical else 1
        assert source == proto.rule_source(trips)
        outputs = []
        for grid in grids:
            h = len(grid)
            period = h - 1
            cycle = list(range(h)) + list(range(h - 2, 0, -1))
            rows = cycle * trips + [0]
            outputs.append([list(grid[index]) for index in rows])
        calls.append({"round_trips": trips, "count": len(grids)})
        return outputs

    return execute


def test_setting_selection_is_typed_deterministic_and_covers_both_settings():
    proto = load_prototype()
    assert proto.setting_for_seed(0) == 1
    assert proto.setting_for_seed(1) == 2
    assert proto.setting_for_seed(18) == proto.setting_for_seed(18)
    assert {proto.setting_for_seed(seed) for seed in range(8)} == {1, 2}
    for value in (-1, True, 1.5, "1", None):
        with pytest.raises(ValueError, match="seed"):
            proto.setting_for_seed(value)


@pytest.mark.parametrize(
    "name,value",
    [
        ("demos", 0),
        ("demos", True),
        ("demos", 17),
        ("queries", 0),
        ("queries", 17),
        ("queries", 1.5),
    ],
)
def test_episode_counts_are_bounded_literal_integers(name, value):
    proto = load_prototype()
    kwargs = {"demos": 3, "queries": 4, name: value}
    with pytest.raises(ValueError, match=name):
        proto.generate_episode(
            0,
            round_trips=1,
            executor=_controlled_executor(proto, []),
            **kwargs,
        )


def test_sample_inputs_are_deterministic_distinct_and_setting_independent():
    proto = load_prototype()
    first = proto.sample_inputs(41, demos=3, queries=4)
    second = proto.sample_inputs(41, demos=3, queries=4)
    assert first == second
    assert len(first) == 7
    fingerprints = {
        json.dumps(grid, sort_keys=True, separators=(",", ":")) for grid in first
    }
    assert len(fingerprints) == 7
    assert all(3 <= len(grid) <= 8 and 9 <= len(grid[0]) <= 21 for grid in first)


@pytest.mark.parametrize("round_trips", [1, 2])
def test_episode_keeps_one_setting_and_demonstrations_refute_the_rival(round_trips):
    proto = load_prototype()
    calls = []
    episode = proto.generate_episode(
        73,
        round_trips=round_trips,
        demos=3,
        queries=4,
        executor=_controlled_executor(proto, calls),
    )
    assert episode["parameters"] == {"round_trips": round_trips}
    assert episode["demo_count"] == 3
    assert episode["query_count"] == 4
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 4
    assert calls == [
        {"round_trips": 1, "count": 7},
        {"round_trips": 2, "count": 7},
    ]
    assert episode["program"] == proto.rule_source(round_trips)
    assert episode["surviving_settings_from_demonstrations"] == [round_trips]
    rival = 2 if round_trips == 1 else 1
    check = episode["rival_checks"][str(rival)]
    assert check["demonstration_mismatches"] == [0, 1, 2]
    assert check["query_disagreements"] == [0, 1, 2, 3]
    assert all(pair["output"] == proto.python_mirror(pair["input"], round_trips)
               for pair in episode["train"] + episode["test"])


def test_episode_uses_seed_selected_setting_when_not_overridden():
    proto = load_prototype()
    for seed in (0, 1):
        episode = proto.generate_episode(
            seed,
            executor=_controlled_executor(proto, []),
        )
        assert episode["parameters"] == {"round_trips": proto.setting_for_seed(seed)}


def test_public_projection_masks_private_fields_and_query_answers():
    from copy import deepcopy
    import hashlib

    proto = load_prototype()
    episode = proto.generate_episode(
        8,
        round_trips=1,
        executor=_controlled_executor(proto, []),
    )
    public = proto.public_payload(episode)
    assert set(public) == {"train", "test"}
    assert len(public["train"]) == 3
    assert len(public["test"]) == 4
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    expected_bytes = public_challenge_bytes(public)
    assert proto.public_bytes(episode) == expected_bytes
    assert proto.public_id(episode) == hashlib.sha256(expected_bytes).hexdigest()

    private_changed = deepcopy(episode)
    private_changed["seed"] = 999
    private_changed["parameters"] = {"round_trips": 2}
    private_changed["program"] = "private replacement"
    private_changed["test"][0]["output"] = [[9]]
    assert proto.public_id(private_changed) == proto.public_id(episode)

    visible_changed = deepcopy(episode)
    visible_changed["test"][0]["input"][0][0] = (
        visible_changed["test"][0]["input"][0][0] + 1
    ) % 10
    assert proto.public_id(visible_changed) != proto.public_id(episode)


def test_public_projection_is_a_deep_copy_of_visible_episode_content():
    proto = load_prototype()
    episode = proto.generate_episode(
        9,
        round_trips=2,
        executor=_controlled_executor(proto, []),
    )
    public = proto.public_payload(episode)
    before = episode["train"][0]["input"][0][0]
    public["train"][0]["input"][0][0] = (before + 1) % 10
    assert episode["train"][0]["input"][0][0] == before


def load_adapter():
    import importlib

    parametric_dir = PROTOTYPE_PATH.parent
    saved_path = list(sys.path)
    previous_prototype = sys.modules.pop("prototype", None)
    previous_adapter = sys.modules.pop("round_trip_adapter_222de43cc4aa", None)
    try:
        sys.path.insert(0, str(parametric_dir))
        spec = importlib.util.spec_from_file_location(
            "round_trip_adapter_222de43cc4aa", parametric_dir / "adapter.py"
        )
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path[:] = saved_path
        if previous_prototype is not None:
            sys.modules["prototype"] = previous_prototype
        else:
            sys.modules.pop("prototype", None)
        if previous_adapter is not None:
            sys.modules["round_trip_adapter_222de43cc4aa"] = previous_adapter


def test_promotion_contract_is_finite_and_defaults_to_exact_canonical_rule():
    proto = load_prototype()
    contract_path = PROTOTYPE_PATH.parent / "promotion.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/222de43cc4aa/workspace/parametric/adapter.py",
        "parameters": {"round_trips": [1, 2]},
        "default": {"round_trips": 2},
        "limits": {"demos": [3, 16], "queries": [1, 16]},
    }
    adapter = load_adapter()
    assert adapter.program(contract["default"]) == canonical_program()
    assert adapter.program({"round_trips": 1}) == proto.rule_source(1)


@pytest.mark.parametrize(
    "settings",
    [
        {},
        {"round_trips": 0},
        {"round_trips": 2, "extra": 1},
        [("round_trips", 2)],
    ],
)
def test_adapter_rejects_malformed_settings(settings):
    adapter = load_adapter()
    with pytest.raises(ValueError, match="settings|round_trips"):
        adapter.program(settings)


def test_adapter_generate_delegates_exact_seed_setting_and_counts(monkeypatch):
    adapter = load_adapter()
    calls = []

    def controlled(seed, round_trips=None, demos=3, queries=4):
        calls.append((seed, round_trips, demos, queries))
        return {"sentinel": [seed, round_trips, demos, queries], "program": "(lambda (g) g)"}

    monkeypatch.setattr(adapter.prototype, "generate_episode", controlled)
    result = adapter.generate(91, {"round_trips": 1}, 5, 6)
    assert result == {
        "sentinel": [91, 1, 5, 6],
        "program": "(lambda (g) g)",
        "program_solution": "(lambda (g) g)",
    }
    assert calls == [(91, 1, 5, 6)]


@pytest.mark.parametrize(
    "demos,queries",
    [
        (1, 4),
        (2, 4),
        (True, 4),
        (3, 0),
        (3, 17),
        (3, True),
    ],
)
def test_adapter_enforces_declared_demo_and_query_limits(monkeypatch, demos, queries):
    adapter = load_adapter()
    monkeypatch.setattr(
        adapter.prototype,
        "generate_episode",
        lambda *args, **kwargs: {"unexpected": True},
    )
    with pytest.raises(ValueError, match="demos|queries"):
        adapter.generate(91, {"round_trips": 1}, demos, queries)


def test_evidence_writer_uses_executor_seam_and_hashes_only_visible_bytes(tmp_path):
    proto = load_prototype()
    calls = []
    destination = tmp_path / "evidence"
    summary = proto.run_evidence(
        destination,
        seeds=[0, 1],
        demos=3,
        queries=4,
        executor=_controlled_executor(proto, calls),
        runtime_identity={
            "schema": "controlled-racket-runtime-v1",
            "backend": "controlled_test_double",
            "protected": True,
        },
    )
    assert summary["status"] == "pass"
    assert summary["episode_application_count"] == 28
    assert summary["canonical_application_count"] >= 3
    assert calls[:4] == [
        {"round_trips": 1, "count": 7},
        {"round_trips": 2, "count": 7},
        {"round_trips": 1, "count": 7},
        {"round_trips": 2, "count": 7},
    ]
    assert calls[-1]["round_trips"] == 2
    public_files = sorted((destination / "public").glob("*.json"))
    assert len(public_files) == 2
    assert all(len(path.stem) == 64 for path in public_files)
    for path in public_files:
        assert path.stem == __import__("hashlib").sha256(path.read_bytes()).hexdigest()
        visible = json.loads(path.read_text(encoding="utf-8"))
        assert len(visible["train"]) == 3
        assert len(visible["test"]) == 4
        assert all("output" not in pair for pair in visible["test"])
        assert path.read_bytes() == public_challenge_bytes(visible)

    private_index = json.loads(
        (destination / "private/index.json").read_text(encoding="utf-8")
    )
    assert {row["parameters"]["round_trips"] for row in private_index["episodes"]} == {1, 2}
    assert proto.verify_evidence(destination)["status"] == "pass"
    with pytest.raises(FileExistsError):
        proto.run_evidence(
            destination,
            seeds=[0, 1],
            executor=_controlled_executor(proto, []),
            runtime_identity={"protected": True},
        )


def test_evidence_verifier_rejects_public_byte_tampering(tmp_path):
    proto = load_prototype()
    destination = tmp_path / "evidence"
    proto.run_evidence(
        destination,
        seeds=[0, 1],
        executor=_controlled_executor(proto, []),
        runtime_identity={"protected": True},
    )
    public_path = next((destination / "public").glob("*.json"))
    visible = json.loads(public_path.read_text(encoding="utf-8"))
    visible["test"][0]["input"][0][0] = (visible["test"][0]["input"][0][0] + 1) % 10
    public_path.write_bytes(public_challenge_bytes(visible))
    with pytest.raises(ValueError, match="hash|public"):
        proto.verify_evidence(destination)


def test_evidence_verifier_rejects_private_query_answer_tampering(tmp_path):
    proto = load_prototype()
    destination = tmp_path / "evidence"
    proto.run_evidence(
        destination,
        seeds=[0, 1],
        executor=_controlled_executor(proto, []),
        runtime_identity={"protected": True},
    )
    index = json.loads((destination / "private/index.json").read_text(encoding="utf-8"))
    private_path = destination / index["episodes"][0]["private_file"]
    episode = json.loads(private_path.read_text(encoding="utf-8"))
    episode["test"][0]["output"][0][0] = (episode["test"][0]["output"][0][0] + 1) % 10
    private_path.write_text(
        json.dumps(episode, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="private.*output|output.*drift"):
        proto.verify_evidence(destination)


def test_evidence_verifier_rejects_manifest_public_id_drift(tmp_path):
    proto = load_prototype()
    destination = tmp_path / "evidence"
    proto.run_evidence(
        destination,
        seeds=[0, 1],
        executor=_controlled_executor(proto, []),
        runtime_identity={"protected": True},
    )
    manifest_path = destination / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["public_ids"] = ["0" * 64, "1" * 64]
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="manifest.*public|public.*manifest"):
        proto.verify_evidence(destination)


@pytest.mark.parametrize("seeds", [[0], [0, 2], [0, 0], [True, 1]])
def test_evidence_requires_one_distinct_seed_per_declared_setting(tmp_path, seeds):
    proto = load_prototype()
    with pytest.raises(ValueError, match="seed|setting"):
        proto.run_evidence(
            tmp_path / ("case-" + "-".join(map(str, seeds))),
            seeds=seeds,
            executor=_controlled_executor(proto, []),
            runtime_identity={"protected": True},
        )
