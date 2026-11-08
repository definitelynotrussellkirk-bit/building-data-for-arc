"""Contract tests for the proposed connector-color parametric prototype."""
from __future__ import annotations

from functools import cache
import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, canonical_path, find_root

TASK_ID = "97dd5f3c96b9"
ROOT = find_root(__file__)
SELECTED_SOURCE = ROOT / "generators" / TASK_ID / "generator.py"
SELECTED_SHA256 = __import__("hashlib").sha256(SELECTED_SOURCE.read_bytes()).hexdigest()
_GEN_SPEC = importlib.util.spec_from_file_location(
    "connector_color_selected_generator", SELECTED_SOURCE
)
assert _GEN_SPEC is not None and _GEN_SPEC.loader is not None
GEN = importlib.util.module_from_spec(_GEN_SPEC)
_GEN_SPEC.loader.exec_module(GEN)
PARAMETRIC = SELECTED_SOURCE.parent / "workspace" / "parametric"
PROTOTYPE = PARAMETRIC / "prototype.py"


@cache
def _load_prototype():
    assert PROTOTYPE.is_file(), "connector-color parametric prototype is not implemented"
    spec = importlib.util.spec_from_file_location(
        "connector_color_parametric_prototype", PROTOTYPE
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    programs = set()
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.add(row["program_solution"])
    assert len(programs) == 1
    return programs.pop()


def _fixture():
    return [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 8, 0, 0, 0, 8, 0, 0, 3, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 3, 0],
        [0, 0, 4, 0, 0, 0, 4, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]


PAIR_COLOR_EXPECTED = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 8, 8, 8, 8, 8, 0, 0, 3, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 3, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 3, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 3, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 3, 0],
    [0, 0, 4, 4, 4, 4, 4, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
]

FIXED_8_EXPECTED = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 8, 8, 8, 8, 8, 0, 0, 3, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 8, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 8, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 8, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 3, 0],
    [0, 0, 4, 8, 8, 8, 4, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
]

FIXED_9_EXPECTED = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 8, 9, 9, 9, 8, 0, 0, 3, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 9, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 9, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 9, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 3, 0],
    [0, 0, 4, 9, 9, 9, 4, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
]


def test_default_program_is_exact_canonical_and_three_settings_are_bounded():
    prototype = _load_prototype()
    assert prototype.CONNECTOR_COLORS == ("pair_color", "fixed_8", "fixed_9")
    assert prototype.DEFAULT_CONNECTOR_COLOR == "pair_color"
    assert prototype.program_for("pair_color") == _canonical_program()
    assert prototype.program_for("fixed_8") != _canonical_program()
    assert prototype.program_for("fixed_9") != _canonical_program()
    assert prototype.program_for("fixed_8") != prototype.program_for("fixed_9")


def test_default_program_matches_all_canonical_pairs_through_racket():
    prototype = _load_prototype()
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge() as bridge:
        for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
            assert (
                prototype.execute_program(
                    bridge, prototype.program_for("pair_color"), pair["input"]
                )
                == pair["output"]
            )


@pytest.mark.parametrize(
    "setting,expected",
    [
        ("pair_color", PAIR_COLOR_EXPECTED),
        ("fixed_8", FIXED_8_EXPECTED),
        ("fixed_9", FIXED_9_EXPECTED),
    ],
)
def test_programs_preserve_endpoints_and_apply_only_declared_interior_color(setting, expected):
    prototype = _load_prototype()
    from arc_repl.racket_bridge import RacketBridge

    grid = _fixture()
    assert GEN.self_check(grid) == []
    assert prototype.python_apply(grid, setting) == expected
    with RacketBridge() as bridge:
        assert prototype.execute_program(bridge, prototype.program_for(setting), grid) == expected


@pytest.mark.parametrize("bad", [None, 8, True, "fixed_7", "PAIR_COLOR"])
def test_invalid_connector_setting_is_rejected(bad):
    prototype = _load_prototype()
    with pytest.raises((TypeError, ValueError), match="connector_color"):
        prototype.program_for(bad)
    with pytest.raises((TypeError, ValueError), match="connector_color"):
        prototype.python_apply(_fixture(), bad)


def _load_adapter():
    path = PARAMETRIC / "adapter.py"
    assert path.is_file(), "promotion adapter is not implemented"
    spec = importlib.util.spec_from_file_location("connector_color_parametric_adapter", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_seed_selection_cycles_over_all_declared_settings():
    prototype = _load_prototype()
    assert [prototype.settings_for_seed(seed) for seed in range(6)] == [
        {"connector_color": "pair_color"},
        {"connector_color": "fixed_8"},
        {"connector_color": "fixed_9"},
        {"connector_color": "pair_color"},
        {"connector_color": "fixed_8"},
        {"connector_color": "fixed_9"},
    ]


@pytest.mark.parametrize("bad", [None, True, 1.5, "3", -1, 2**63])
def test_seed_validation_is_exact_and_bounded(bad):
    prototype = _load_prototype()
    with pytest.raises((TypeError, ValueError), match="seed"):
        prototype.settings_for_seed(bad)
    with pytest.raises((TypeError, ValueError), match="seed"):
        prototype.generate_episode(bad, "pair_color", demos=2, queries=4)


@pytest.mark.parametrize("name", ["demos", "queries"])
@pytest.mark.parametrize("bad", [None, True, 1.5, "4", 0, 17])
def test_demo_and_query_count_validation_is_independent(name, bad):
    prototype = _load_prototype()
    kwargs = {"demos": 2, "queries": 4}
    kwargs[name] = bad
    with pytest.raises((TypeError, ValueError), match=name):
        prototype.generate_episode(0, "pair_color", **kwargs)


def test_episode_replays_exactly_and_inputs_do_not_depend_on_setting():
    prototype = _load_prototype()
    episodes = {
        setting: prototype.generate_episode(23, setting, demos=2, queries=4)
        for setting in prototype.CONNECTOR_COLORS
    }
    assert episodes["fixed_8"] == prototype.generate_episode(
        23, "fixed_8", demos=2, queries=4
    )
    input_vectors = [_inputs(episodes[setting]) for setting in prototype.CONNECTOR_COLORS]
    assert input_vectors[0] == input_vectors[1] == input_vectors[2]
    assert len({json.dumps(grid, separators=(",", ":")) for grid in input_vectors[0]}) == 6
    for setting, episode in episodes.items():
        assert set(episode) == {"train", "test", "program_solution"}
        assert len(episode["train"]) == 2
        assert len(episode["test"]) == 4
        assert episode["program_solution"] == prototype.program_for(setting)
        for pair in episode["train"] + episode["test"]:
            assert pair["output"] == prototype.python_apply(pair["input"], setting)


@pytest.mark.parametrize("demos,queries", [(1, 16), (16, 1), (16, 16)])
def test_episode_supports_count_boundaries_with_distinct_lawful_inputs(demos, queries):
    prototype = _load_prototype()
    episode = prototype.generate_episode(91, "fixed_9", demos=demos, queries=queries)
    inputs = _inputs(episode)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == queries
    assert len(inputs) == demos + queries
    assert len({json.dumps(grid, separators=(",", ":")) for grid in inputs}) == len(inputs)
    assert {tuple(map(len, (grid, grid[0]))) for grid in inputs} == {
        (8, 10),
        (9, 11),
        (8, 12),
    }
    assert all(GEN.self_check(grid) == [] for grid in inputs)


def test_promotion_adapter_and_contract_are_exact_and_thin():
    prototype = _load_prototype()
    adapter = _load_adapter()
    promotion_path = PARAMETRIC / "promotion.json"
    assert promotion_path.is_file()
    promotion = json.loads(promotion_path.read_text(encoding="utf-8"))
    assert promotion == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/97dd5f3c96b9/workspace/parametric/adapter.py",
        "parameters": {
            "connector_color": ["pair_color", "fixed_8", "fixed_9"]
        },
        "default": {"connector_color": "pair_color"},
        "limits": {"demos": [1, 16], "queries": [1, 16]},
        "resources": [
            "generators/97dd5f3c96b9/workspace/parametric/prototype.py"
        ],
    }
    for setting in prototype.CONNECTOR_COLORS:
        settings = {"connector_color": setting}
        assert adapter.program(settings) == prototype.program_for(setting)
        assert adapter.generate(17, settings, 2, 4) == prototype.generate_episode(
            17, setting, demos=2, queries=4
        )
    for bad in ({}, {"connector_color": "fixed_8", "extra": 1}, None):
        with pytest.raises((TypeError, ValueError), match="settings"):
            adapter.program(bad)


def test_evidence_writer_emits_hash_named_public_challenges_and_private_racket_receipts(tmp_path):
    prototype = _load_prototype()
    from reviewer_support import public_challenge_bytes, public_challenge_id

    out = tmp_path / "connector-color-evidence"
    manifest = prototype.write_evidence(
        out, seeds=[0, 1, 2], demos=2, queries=4
    )
    assert manifest == json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema"] == "97dd5f3c96b9-connector-color-evidence-v1"
    assert manifest["status"] == prototype.STATUS
    assert manifest["racket"]["backend"] == "racket"
    assert manifest["racket"]["protected"] is True
    assert len(manifest["episodes"]) == 3

    public_paths = sorted((out / "public").glob("challenge-*.json"))
    private_paths = sorted((out / "private").glob("challenge-*.json"))
    rule_paths = sorted((out / "rules").glob("*.rkt"))
    assert len(public_paths) == len(private_paths) == len(rule_paths) == 3
    assert {path.stem for path in rule_paths} == set(prototype.CONNECTOR_COLORS)
    assert {
        path.read_text(encoding="utf-8")
        for path in rule_paths
    } == {prototype.program_for(setting) for setting in prototype.CONNECTOR_COLORS}

    settings_seen = set()
    private_by_id = {}
    for path in private_paths:
        private = json.loads(path.read_text(encoding="utf-8"))
        private_by_id[private["public_id"]] = private
        settings_seen.add(private["settings"]["connector_color"])
        assert private["runtime_identity"]["protected"] is True
        assert len(private["query_answers"]) == 4
        chosen = private["settings"]["connector_color"]
        survivors = [
            setting
            for setting, check in private["rival_checks"].items()
            if check["matches_all_demonstrations"]
        ]
        assert survivors == [chosen]
        for setting, check in private["rival_checks"].items():
            if setting != chosen:
                assert check["query_disagreement_indices"] == [0, 1, 2, 3]
    assert settings_seen == set(prototype.CONNECTOR_COLORS)

    for path in public_paths:
        public = json.loads(path.read_text(encoding="utf-8"))
        identifier = public_challenge_id(public)
        assert path.name == f"challenge-{identifier}.json"
        assert path.read_bytes() == public_challenge_bytes(public)
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert all(set(pair) == {"input"} for pair in public["test"])
        raw = path.read_text(encoding="utf-8")
        for forbidden in (
            "connector_color",
            "pair_color",
            "fixed_8",
            "fixed_9",
            "program_solution",
            "query_answers",
            '"seed"',
        ):
            assert forbidden not in raw
        assert identifier in private_by_id
        assert private_by_id[identifier]["public_sha256"] == identifier


def test_evidence_writer_rejects_duplicate_visible_challenges_before_creating_output(tmp_path):
    prototype = _load_prototype()
    out = tmp_path / "must-not-exist"
    with pytest.raises(ValueError, match="duplicate visible"):
        prototype.write_evidence(out, seeds=[5, 5], demos=2, queries=4)
    assert not out.exists()


def test_evidence_writer_refuses_existing_destination(tmp_path):
    prototype = _load_prototype()
    out = tmp_path / "already-there"
    out.mkdir()
    sentinel = out / "keep.txt"
    sentinel.write_text("unchanged", encoding="utf-8")
    with pytest.raises(FileExistsError, match="already exists"):
        prototype.write_evidence(out, seeds=[0], demos=2, queries=4)
    assert sentinel.read_text(encoding="utf-8") == "unchanged"
