from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest

from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "cf4fdf474ad5"
ROOT = find_root(__file__)
TASK_HOME = ROOT / "generators" / TASK_ID
PARAMETRIC = TASK_HOME / "workspace" / "parametric"
PROTOTYPE_PATH = PARAMETRIC / "prototype.py"
GEN, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def _load_module(path: Path, name: str):
    assert path.is_file(), f"expected implementation file: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_prototype():
    return _load_module(PROTOTYPE_PATH, "cf4fdf474ad5_height_threshold_prototype")


def _load_adapter():
    return _load_module(
        PARAMETRIC / "adapter.py", "cf4fdf474ad5_height_threshold_adapter"
    )


def _canonical_program() -> str:
    programs: set[str] = set()
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.add(row["program_solution"])
    assert len(programs) == 1
    return programs.pop()


def _paint(
    grid: list[list[int]],
    *,
    top: int,
    left: int,
    height: int,
    width: int,
    green: int,
) -> list[list[int]]:
    cells = [(r, c) for r in range(top, top + height) for c in range(left, left + width)]
    assert 0 < green < len(cells)
    for r, c in cells:
        grid[r][c] = 8
    for r, c in cells[:green]:
        grid[r][c] = 3
    return [row[left : left + width] for row in grid[top : top + height]]


def _threshold_fixture() -> tuple[list[list[int]], dict[int, list[list[int]]]]:
    grid = [[0] * 22 for _ in range(22)]
    expected = {
        5: _paint(grid, top=0, left=0, height=5, width=7, green=3),
        8: _paint(grid, top=0, left=9, height=8, width=9, green=5),
        9: _paint(grid, top=12, left=0, height=9, width=10, green=7),
    }
    assert GEN.self_check(grid) == []
    return grid, expected


def _episode_inputs(episode: dict[str, Any]) -> list[list[list[int]]]:
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_default_program_is_exact_canonical_and_alternatives_change_only_threshold():
    prototype = _load_prototype()
    canonical = _canonical_program()
    assert prototype.HEIGHT_LIMITS == (5, 8, 9)
    assert prototype.DEFAULT_MAX_HEIGHT == 8
    assert canonical.count("(<= hh 8)") == 1
    assert prototype.program_for(8) == canonical
    assert prototype.program_for(5) == canonical.replace("(<= hh 8)", "(<= hh 5)")
    assert prototype.program_for(9) == canonical.replace("(<= hh 8)", "(<= hh 9)")


@pytest.mark.parametrize("bad", [None, True, 5.0, "8", 4, 6, 10])
def test_invalid_height_setting_is_rejected(bad):
    prototype = _load_prototype()
    with pytest.raises((TypeError, ValueError), match="max_height"):
        prototype.program_for(bad)
    with pytest.raises((TypeError, ValueError), match="max_height"):
        prototype.python_apply(_threshold_fixture()[0], bad)


@pytest.mark.parametrize("max_height", [5, 8, 9])
def test_python_and_racket_apply_exact_height_boundary(max_height):
    prototype = _load_prototype()
    grid, expected = _threshold_fixture()
    assert prototype.python_apply(grid, max_height) == expected[max_height]

    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge() as bridge:
        assert (
            prototype.execute_program(bridge, prototype.program_for(max_height), grid)
            == expected[max_height]
        )


def test_default_program_matches_all_canonical_pairs_through_racket():
    prototype = _load_prototype()
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge() as bridge:
        for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
            assert (
                prototype.execute_program(bridge, prototype.program_for(8), pair["input"])
                == pair["output"]
            )


def test_seed_selection_cycles_over_all_declared_settings():
    prototype = _load_prototype()
    assert [prototype.settings_for_seed(seed) for seed in range(6)] == [
        {"max_height": 5},
        {"max_height": 8},
        {"max_height": 9},
        {"max_height": 5},
        {"max_height": 8},
        {"max_height": 9},
    ]


@pytest.mark.parametrize("bad", [None, True, 1.5, "3", -1, 2**63])
def test_seed_validation_is_exact_and_bounded(bad):
    prototype = _load_prototype()
    with pytest.raises((TypeError, ValueError), match="seed"):
        prototype.settings_for_seed(bad)
    with pytest.raises((TypeError, ValueError), match="seed"):
        prototype.generate_episode(bad, 8, demos=1, queries=4)


@pytest.mark.parametrize("name", ["demos", "queries"])
@pytest.mark.parametrize("bad", [None, True, 1.5, "4", 0, 17])
def test_demo_and_query_count_validation_is_independent(name, bad):
    prototype = _load_prototype()
    kwargs = {"demos": 1, "queries": 4}
    kwargs[name] = bad
    with pytest.raises((TypeError, ValueError), match=name):
        prototype.generate_episode(0, 8, **kwargs)


def test_episode_replays_exactly_and_inputs_do_not_depend_on_setting():
    prototype = _load_prototype()
    episodes = {
        setting: prototype.generate_episode(23, setting, demos=2, queries=4)
        for setting in prototype.HEIGHT_LIMITS
    }
    assert episodes[8] == prototype.generate_episode(23, 8, demos=2, queries=4)
    input_vectors = [_episode_inputs(episodes[setting]) for setting in prototype.HEIGHT_LIMITS]
    assert input_vectors[0] == input_vectors[1] == input_vectors[2]
    assert len({json.dumps(grid, separators=(",", ":")) for grid in input_vectors[0]}) == 6

    for setting, episode in episodes.items():
        assert set(episode) == {"train", "test", "program_solution"}
        assert len(episode["train"]) == 2
        assert len(episode["test"]) == 4
        assert episode["program_solution"] == prototype.program_for(setting)
        for pair in episode["train"] + episode["test"]:
            assert pair["output"] == prototype.python_apply(pair["input"], setting)
            assert GEN.self_check(pair["input"]) == []


@pytest.mark.parametrize("demos,queries", [(1, 16), (16, 1), (16, 16)])
def test_episode_supports_count_boundaries_with_distinct_lawful_inputs(demos, queries):
    prototype = _load_prototype()
    episode = prototype.generate_episode(91, 9, demos=demos, queries=queries)
    inputs = _episode_inputs(episode)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == queries
    assert len(inputs) == demos + queries
    assert len({json.dumps(grid, separators=(",", ":")) for grid in inputs}) == len(inputs)
    assert all(GEN.self_check(grid) == [] for grid in inputs)


def test_demo_and_query_stream_prefixes_are_independent():
    prototype = _load_prototype()
    short_queries = prototype.generate_episode(17, 8, demos=3, queries=1)
    long_queries = prototype.generate_episode(17, 8, demos=3, queries=6)
    assert [p["input"] for p in short_queries["train"]] == [
        p["input"] for p in long_queries["train"]
    ]
    assert [p["input"] for p in short_queries["test"]] == [
        p["input"] for p in long_queries["test"][:1]
    ]

    short_demos = prototype.generate_episode(17, 8, demos=1, queries=4)
    long_demos = prototype.generate_episode(17, 8, demos=6, queries=4)
    assert [p["input"] for p in short_demos["train"]] == [
        p["input"] for p in long_demos["train"][:1]
    ]
    assert [p["input"] for p in short_demos["test"]] == [
        p["input"] for p in long_demos["test"]
    ]


@pytest.mark.parametrize("setting", [5, 8, 9])
def test_one_demonstration_identifies_setting_and_queries_separate_all_settings(setting):
    prototype = _load_prototype()
    episode = prototype.generate_episode(101, setting, demos=1, queries=4)
    certificate = prototype.identify_setting(episode["train"])
    assert certificate["survivors"] == [setting]
    assert set(certificate["mismatching_demonstrations"]) == {5, 8, 9}
    assert certificate["mismatching_demonstrations"][setting] == []
    assert all(
        certificate["mismatching_demonstrations"][other] == [0]
        for other in prototype.HEIGHT_LIMITS
        if other != setting
    )
    for pair in episode["test"]:
        predictions = {
            other: prototype.python_apply(pair["input"], other)
            for other in prototype.HEIGHT_LIMITS
        }
        assert len({json.dumps(value, separators=(",", ":")) for value in predictions.values()}) == 3


def test_promotion_adapter_and_contract_are_exact_and_thin():
    prototype = _load_prototype()
    adapter = _load_adapter()
    promotion = json.loads((PARAMETRIC / "promotion.json").read_text(encoding="utf-8"))
    assert promotion == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/cf4fdf474ad5/workspace/parametric/adapter.py",
        "parameters": {"max_height": [5, 8, 9]},
        "default": {"max_height": 8},
        "limits": {"demos": [1, 16], "queries": [1, 16]},
        "resources": [
            "generators/cf4fdf474ad5/workspace/parametric/prototype.py"
        ],
    }
    for setting in prototype.HEIGHT_LIMITS:
        settings = {"max_height": setting}
        assert adapter.program(settings) == prototype.program_for(setting)
        assert adapter.generate(17, settings, 2, 4) == prototype.generate_episode(
            17, setting, demos=2, queries=4
        )
    for bad in ({}, {"max_height": 8, "extra": 1}, None):
        with pytest.raises((TypeError, ValueError), match="settings"):
            adapter.program(bad)


def test_public_projection_and_id_ignore_private_fields_and_query_answers():
    prototype = _load_prototype()
    episode = prototype.generate_episode(3, 8, demos=1, queries=4)
    public_before = prototype.public_projection(episode)
    public_bytes_before = public_challenge_bytes(public_before)
    public_id_before = public_challenge_id(public_before)

    mutated = copy.deepcopy(episode)
    mutated["program_solution"] = "private program changed"
    mutated["private_settings"] = {"max_height": 5}
    mutated["test"][0]["output"][0][0] = (mutated["test"][0]["output"][0][0] + 1) % 10
    public_after = prototype.public_projection(mutated)
    assert public_challenge_bytes(public_after) == public_bytes_before
    assert public_challenge_id(public_after) == public_id_before


def test_evidence_writer_emits_hash_named_public_challenges_and_private_racket_receipts(tmp_path):
    prototype = _load_prototype()
    out = tmp_path / "height-threshold-evidence"
    manifest = prototype.write_evidence(out, seeds=[0, 1, 2], demos=1, queries=4)
    assert manifest == json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema"] == "cf4fdf474ad5-height-threshold-evidence-v1"
    assert manifest["status"] == prototype.STATUS
    assert manifest["racket"]["backend"] == "racket"
    assert manifest["racket"]["protected"] is True
    assert len(manifest["episodes"]) == 3

    public_paths = sorted((out / "public").glob("*.json"))
    private_paths = sorted((out / "private").glob("*.json"))
    rule_paths = sorted((out / "rules").glob("max-height-*.rkt"))
    assert len(public_paths) == len(private_paths) == len(rule_paths) == 3
    assert {path.stem for path in rule_paths} == {
        "max-height-5",
        "max-height-8",
        "max-height-9",
    }

    settings_seen = set()
    for public_path in public_paths:
        public = json.loads(public_path.read_text(encoding="utf-8"))
        assert public_path.stem == public_challenge_id(public)
        assert public_path.read_bytes() == public_challenge_bytes(public)
        text = public_path.read_text(encoding="utf-8")
        assert "max_height" not in text
        assert "program_solution" not in text
        assert "query_outputs" not in text

    for private_path in private_paths:
        private = json.loads(private_path.read_text(encoding="utf-8"))
        settings_seen.add(private["settings"]["max_height"])
        assert private["runtime_identity"]["protected"] is True
        assert len(private["query_outputs"]) == 4
        assert private["identification"]["survivors"] == [
            private["settings"]["max_height"]
        ]
        assert private["source_sha256"]["generator.py"] == GENERATOR_SHA256
        public = json.loads((out / "public" / f"{private['public_id']}.json").read_text())
        assert public_challenge_id(public) == private["public_id"]
    assert settings_seen == {5, 8, 9}

    with pytest.raises(FileExistsError):
        prototype.write_evidence(out, seeds=[0], demos=1, queries=4)


def test_evidence_writer_rejects_duplicate_visible_payload_before_creating_destination(tmp_path):
    prototype = _load_prototype()
    out = tmp_path / "duplicates"
    with pytest.raises(ValueError, match="duplicate visible"):
        prototype.write_evidence(out, seeds=[0, 0], demos=1, queries=4)
    assert not out.exists()
