from __future__ import annotations

import copy
import importlib.util
import json
from functools import cache
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "c690e739e0ce"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def _load(filename: str, name: str):
    path = HOME / filename
    assert path.is_file(), f"missing parametric artifact: {path.relative_to(ROOT)}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@cache
def proto():
    return _load("prototype.py", "_c690e739_parametric")


@cache
def adapter():
    return _load("adapter.py", "_c690e739_adapter")


def _canonical_program() -> str:
    for line in canonical_path(ROOT).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise AssertionError(TASK_ID)


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_default_program_is_exact_canonical_and_alternate_is_distinct():
    p = proto()
    assert p.DEFAULT == {"reflection_scope": "all_rows"}
    assert p.program(p.DEFAULT) == _canonical_program()
    alternate = p.program({"reflection_scope": "minority_rows"})
    assert alternate != _canonical_program()
    assert len({p.program(setting) for setting in p.SETTINGS}) == 2


def test_minority_intermediate_controls_which_complete_rows_reflect():
    p = proto()
    grid = [
        [1, 2, 3, 4, 1, 2],
        [3, 9, 4, 1, 2, 3],
        [4, 1, 2, 3, 4, 1],
        [2, 3, 4, 1, 9, 2],
        [1, 4, 3, 2, 1, 4],
        [3, 2, 1, 4, 3, 2],
    ]
    before = copy.deepcopy(grid)
    profile = p.input_profile(grid)
    assert profile["minority_color"] == 9
    assert profile["selected_rows"] == (1, 3)

    all_rows = p.transform(grid, {"reflection_scope": "all_rows"})
    minority = p.transform(grid, {"reflection_scope": "minority_rows"})
    assert grid == before
    assert all_rows[0] == grid[0][::-1]
    assert minority[0] == grid[0]
    assert minority[1] == grid[1][::-1]
    assert minority[3] == grid[3][::-1]
    assert minority != all_rows


def test_two_demo_minimum_identifies_setting_and_rejects_named_shortcuts():
    p = proto()
    for setting in p.SETTINGS:
        episode = p.generate(17, setting, demos=2, queries=4)
        certificate = episode["certificate"]
        assert certificate["survivors"] == [setting]
        assert set(certificate["extra_refutations"]) == set(p.EXTRA_RIVALS)
        assert all(indices for indices in certificate["extra_refutations"].values())
        assert len({row["minority_color"] for row in certificate["demo_profiles"]}) == 2
        assert any(row["selected_rows"] != certificate["demo_profiles"][0]["selected_rows"]
                   for row in certificate["demo_profiles"][1:])


@pytest.mark.parametrize("demos", [2, 3, 6])
@pytest.mark.parametrize("scope", ["all_rows", "minority_rows"])
def test_generation_is_deterministic_matched_and_count_independent(demos, scope):
    p = proto()
    setting = {"reflection_scope": scope}
    episode = p.generate(29, setting, demos=demos, queries=4)
    assert episode == p.generate(29, setting, demos=demos, queries=4)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == 4
    assert len({p.digest(grid) for grid in _inputs(episode)}) == demos + 4

    other = p.generate(
        29,
        {"reflection_scope": "minority_rows" if scope == "all_rows" else "all_rows"},
        demos=demos,
        queries=4,
    )
    assert _inputs(episode) == _inputs(other)
    assert any(a["output"] != b["output"] for a, b in zip(episode["train"], other["train"]))

    short = p.generate(29, setting, demos=2, queries=4)
    long = p.generate(29, setting, demos=6, queries=4)
    assert short["train"] == long["train"][:2]
    assert short["test"] == long["test"]


def test_query_schedule_has_substantive_30x30_stress_and_crossed_rows():
    p = proto()
    episode = p.generate(41, {"reflection_scope": "minority_rows"}, demos=3, queries=4)
    sizes = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert sizes == [(8, 11), (13, 17), (22, 26), (30, 30)]
    large = episode["test"][-1]["input"]
    profile = p.input_profile(large)
    assert len(profile["selected_rows"]) >= 6
    assert len(profile["unselected_rows"]) >= 6
    assert profile["minority_count"] >= 6
    assert profile["asymmetric_row_count"] == 30
    assert len({cell for row in large for cell in row}) >= 5


def test_public_projection_hides_settings_answers_future_queries_and_total_count():
    p = proto()
    episode = p.generate(59, p.DEFAULT, demos=3, queries=4)
    view = p.public_turn(episode, 0)
    assert set(view) == {"train", "test"}
    assert len(view["test"]) == 1 and set(view["test"][0]) == {"input"}
    assert all(set(pair) == {"input", "output"} for pair in view["train"])
    body = public_challenge_bytes(view)
    identifier = public_challenge_id(view)

    changed = copy.deepcopy(episode)
    changed["settings"] = {"reflection_scope": "minority_rows"}
    changed["program_solution"] = "private"
    changed["test"][0]["output"] = [[9]]
    changed["test"][1]["input"] = [[9]]
    assert public_challenge_bytes(p.public_turn(changed, 0)) == body
    assert public_challenge_id(p.public_turn(changed, 0)) == identifier
    for forbidden in (b"settings", b"program", b"query_index", b"query_count"):
        assert forbidden not in body


def test_certificate_and_writer_fail_closed_on_tampering_and_duplicates(tmp_path):
    p = proto()
    episode = p.generate(67, {"reflection_scope": "minority_rows"}, demos=2, queries=4)
    tampered = copy.deepcopy(episode)
    tampered["train"][0]["output"][0][0] = (tampered["train"][0]["output"][0][0] + 1) % 10
    with pytest.raises(ValueError):
        p.certify(tampered)

    duplicate = copy.deepcopy(episode)
    duplicate["private_note"] = "different"
    destination = tmp_path / "duplicate"
    with pytest.raises(ValueError, match="distinct first-turn challenges"):
        p.write_batch([episode, duplicate], destination)
    assert not destination.exists()


def test_adapter_contract_and_strict_parameter_boundaries():
    p = proto()
    a = adapter()
    promotion = json.loads((HOME / "promotion.json").read_text())
    assert promotion["default"] == p.DEFAULT
    assert promotion["limits"] == {"demos": [2, 6], "queries": [4, 4]}
    episode = a.generate(5, {"reflection_scope": "minority_rows"}, 6, 4)
    assert (len(episode["train"]), len(episode["test"])) == (6, 4)
    assert episode["program_solution"] == a.program({"reflection_scope": "minority_rows"})

    for settings in ({}, {"reflection_scope": "other"}, {"reflection_scope": 1},
                     {"reflection_scope": "all_rows", "extra": 1}):
        with pytest.raises(ValueError):
            p.program(settings)
    for key, value in (("seed", True), ("demos", 1), ("demos", 7),
                       ("queries", 1), ("queries", 5), ("queries", True)):
        kwargs = dict(seed=9, settings=p.DEFAULT, demos=3, queries=4)
        kwargs[key] = value
        with pytest.raises(ValueError):
            p.generate(**kwargs)


def test_protected_racket_matches_python_mirror_for_both_settings():
    p = proto()
    episode = p.generate(73, p.DEFAULT, demos=2, queries=4)
    with p.RacketRunner() as execute:
        for setting in p.SETTINGS:
            for pair in episode["train"] + episode["test"]:
                assert execute(p.program(setting), pair["input"]) == p.transform(pair["input"], setting)


def test_adversarial_probe_finds_no_query_changing_survivor_in_bounded_search():
    probe = _load("adversarial_probe.py", "_c690e739_adversarial")
    report = probe.audit(seeds=range(8), demo_counts=(2, 3), use_racket=False)
    assert report["cases"] == 8 * 2 * 2
    assert report["query_changing_survivors"] == []
    assert report["distribution_equivalent_survivors"] == []
    assert report["certificate_tamper_checks"]["all_rejected"] is True
    assert report["public_projection_checks"]["all_passed"] is True


def test_causal_witness_carries_replayable_input_programs_and_outputs():
    p = proto()
    grid = p._scene(101, "query", 3)
    witness = p.causal_witness(grid)
    assert witness["input"] == grid
    assert witness["correct_program"] == p.program({"reflection_scope": "minority_rows"})
    assert witness["counterfactual_program"] != witness["correct_program"]
    assert witness["correct_output"] != witness["counterfactual_output"]
    assert witness["correct_output_sha256"] == p.digest(witness["correct_output"])
    assert witness["counterfactual_output_sha256"] == p.digest(witness["counterfactual_output"])
