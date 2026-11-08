"""Focused tests for the c2f4b540f2fb local-tier parametric family."""
from __future__ import annotations

import copy
from functools import cache
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes

TASK_ID = "c2f4b540f2fb"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def _load(path: Path, name: str):
    assert path.is_file(), f"missing {path.relative_to(ROOT)}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@cache
def prototype():
    return _load(HOME / "prototype.py", "_c2f4b540f2fb_parametric")


@cache
def adapter():
    return _load(HOME / "adapter.py", "_c2f4b540f2fb_adapter")


def _canonical_program() -> str:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        programs = {
            row["program_solution"]
            for line in handle
            for row in [json.loads(line)]
            if row.get("task_id") == TASK_ID and isinstance(row.get("program_solution"), str)
        }
    assert len(programs) == 1
    return next(iter(programs))


def _inputs(episode: dict) -> list[list[list[int]]]:
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_default_program_is_exact_canonical_and_all_four_settings_are_distinct() -> None:
    p = prototype()
    assert p.program(p.DEFAULT_SETTINGS) == _canonical_program()
    assert (HOME / "canonical.rkt").read_text(encoding="utf-8") == _canonical_program()
    programs = {p.program(setting) for setting in p.SETTINGS}
    assert len(programs) == 4
    assert all(text.startswith("(rule!") for text in programs)
    assert adapter().program(copy.deepcopy(p.DEFAULT_SETTINGS)) == _canonical_program()


@pytest.mark.parametrize("demos", [2, 3, 6])
@pytest.mark.parametrize("settings", [
    {"axis": "u", "extreme": "max"},
    {"axis": "u", "extreme": "min"},
    {"axis": "v", "extreme": "max"},
    {"axis": "v", "extreme": "min"},
])
def test_episode_counts_distinct_inputs_demo_identification_and_shortcut_refutation(
    demos: int, settings: dict[str, str]
) -> None:
    p = prototype()
    episode = p.generate(7000 + demos, settings, demos, 4)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == 4
    assert episode["settings"] == settings
    assert episode["program_solution"] == p.program(settings)
    assert len({p.grid_digest(grid) for grid in _inputs(episode)}) == demos + 4
    certificate = p.certify(episode)
    assert certificate["survivors"] == [settings]
    assert set(certificate["extra_refutations"]) == set(p.EXTRA_RIVALS)
    assert all(certificate["extra_refutations"].values())


def test_same_seed_and_counts_use_identical_inputs_across_settings() -> None:
    p = prototype()
    episodes = [p.generate(314159, setting, 3, 4) for setting in p.SETTINGS]
    baseline = _inputs(episodes[0])
    assert all(_inputs(episode) == baseline for episode in episodes[1:])
    assert len({json.dumps([pair["output"] for pair in episode["train"]]) for episode in episodes}) == 4


def test_queries_cover_ties_rotated_frames_boundary_contacts_and_substantive_30x30() -> None:
    p = prototype()
    episode = p.generate(271828, p.DEFAULT_SETTINGS, 3, 4)
    profiles = [p.scene_profile(pair["input"]) for pair in episode["test"]]
    assert profiles[-1]["size"] == [30, 30]
    assert profiles[-1]["occupied_quadrants"] == [0, 1, 2, 3]
    assert profiles[-1]["nonzero_count"] >= 35
    assert any(profile["selected_tie_counts"]["max_u"] > 1 for profile in profiles)
    assert any(profile["source_basis"] != profile["target_basis"] for profile in profiles)
    assert any(profile["touches_boundary"] for profile in profiles)
    assert len({tuple(profile["source_basis"]) for profile in profiles}) >= 2


def test_shared_30x30_query_distinguishes_every_declared_setting() -> None:
    p = prototype()
    episodes = [p.generate(0, setting, 2, 4) for setting in p.SETTINGS]
    shared = episodes[0]["test"][-1]["input"]
    assert all(episode["test"][-1]["input"] == shared for episode in episodes[1:])
    outputs = {json.dumps(p.transform(shared, setting)) for setting in p.SETTINGS}
    assert len(outputs) == len(p.SETTINGS)


def test_transform_is_input_pure_and_adapter_returns_only_native_fields() -> None:
    p = prototype()
    episode = p.generate(12345, {"axis": "v", "extreme": "min"}, 2, 4)
    grid = copy.deepcopy(episode["test"][0]["input"])
    snapshot = copy.deepcopy(grid)
    out = p.transform(grid, episode["settings"])
    assert grid == snapshot
    assert out == episode["test"][0]["output"]
    native = adapter().generate(12345, episode["settings"], 2, 4)
    assert set(native) == {"train", "test", "program_solution"}


@pytest.mark.parametrize(
    "call",
    [
        lambda p: p.generate(True, p.DEFAULT_SETTINGS, 2, 4),
        lambda p: p.generate(1, {"axis": "u"}, 2, 4),
        lambda p: p.generate(1, {"axis": "x", "extreme": "max"}, 2, 4),
        lambda p: p.generate(1, p.DEFAULT_SETTINGS, True, 4),
        lambda p: p.generate(1, p.DEFAULT_SETTINGS, 1, 4),
        lambda p: p.generate(1, p.DEFAULT_SETTINGS, 2, 3),
        lambda p: p.program({"axis": "u", "extreme": True}),
    ],
)
def test_malformed_typed_arguments_reject_loudly(call) -> None:
    with pytest.raises(ValueError):
        call(prototype())


def test_public_turn_contains_no_private_settings_program_or_future_queries() -> None:
    p = prototype()
    episode = p.generate(444, {"axis": "u", "extreme": "min"}, 3, 4)
    first = p.public_turn(episode, 0)
    assert set(first) == {"train", "test"}
    assert len(first["test"]) == 1
    assert set(first["test"][0]) == {"input"}
    body = public_challenge_bytes(first)
    assert b"settings" not in body and b"program" not in body and b"output" in body
    assert episode["test"][1]["input"] not in [pair["input"] for pair in first["test"]]


def test_python_mirror_matches_protected_racket_on_teaching_and_30x30_cases() -> None:
    p = prototype()
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    wrapped: dict[str, str] = {}
    with RacketBridge(max_calls_before_restart=128) as bridge:
        assert bridge.runtime_identity.get("backend") == "racket"
        assert bridge.runtime_identity.get("protected") is True
        for setting in p.SETTINGS:
            episode = p.generate(99, setting, 2, 4)
            source = p.program(setting)
            wrapped.setdefault(source, wrap_rule(source))
            for pair in [episode["train"][0], episode["test"][-1]]:
                literal = "'(" + " ".join(
                    "(" + " ".join(map(str, row)) + ")" for row in pair["input"]
                ) + ")"
                actual = bridge.eval_text(f"({wrapped[source]} {literal})")
                assert actual == pair["output"] == p.transform(pair["input"], setting)


def test_canonical_program_file_has_stable_exact_hash() -> None:
    expected = hashlib.sha256(_canonical_program().encode("utf-8")).hexdigest()
    assert hashlib.sha256((HOME / "canonical.rkt").read_bytes()).hexdigest() == expected
