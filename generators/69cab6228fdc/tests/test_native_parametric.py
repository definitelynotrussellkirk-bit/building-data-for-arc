"""Native adapter contract and boundary regressions for 69cab6228fdc."""
from __future__ import annotations

import importlib.util

import pytest
from arcpuzzles import Catalog
from reviewer_support import find_root

TASK_ID = "69cab6228fdc"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def load_adapter():
    path = HOME / "adapter.py"
    assert path.is_file(), "native adapter is missing"
    spec = importlib.util.spec_from_file_location("native_69cab6228fdc_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_program_is_exact_selected_canonical_source():
    module = load_adapter()
    programs = {row["program_solution"] for row in Catalog(ROOT).get(TASK_ID)["variants"]}
    assert programs == {module.program({"recolor_scope": "all_sources"})}
    assert module.program({"recolor_scope": "most_frequent_source"}) not in programs


def test_settings_share_inputs_and_alternative_uses_unique_most_frequent_source():
    module = load_adapter()
    canonical = module.generate(17, {"recolor_scope": "all_sources"}, 3, 4)
    selective = module.generate(17, {"recolor_scope": "most_frequent_source"}, 3, 4)
    for split in ("train", "test"):
        assert [pair["input"] for pair in canonical[split]] == [pair["input"] for pair in selective[split]]
    for all_pair, selective_pair in zip(canonical["train"], selective["train"], strict=True):
        facts = module.analyze(all_pair["input"])
        selected = facts["most_frequent_source"]
        mapping = facts["mapping"]
        body = all_pair["input"][3:]
        expected = [[mapping[value] if value == selected else value for value in row] for row in body]
        assert selective_pair["output"] == expected
        assert all_pair["output"] != selective_pair["output"]


def test_counts_are_prefix_stable_and_fourth_query_is_substantive_30x30():
    module = load_adapter()
    settings = {"recolor_scope": "most_frequent_source"}
    small = module.generate(71, settings, 2, 1)
    large = module.generate(71, settings, 6, 4)
    assert small["train"] == large["train"][:2]
    assert small["test"] == large["test"][:1]
    assert len({repr(pair["input"]) for pair in large["train"] + large["test"]}) == 10
    stress = large["test"][3]["input"]
    assert (len(stress), len(stress[0])) == (30, 30)
    facts = module.analyze(stress)
    assert facts["n_pairs"] == 3
    assert facts["body_nonzero"] >= 280
    assert len(facts["source_counts"]) == 3


def test_public_turn_reveals_one_query_and_no_private_fields():
    module = load_adapter()
    episode = module.generate(3, {"recolor_scope": "all_sources"}, 2, 4)
    visible = module.public_turn(episode, 2)
    assert set(visible) == {"train", "test"}
    assert len(visible["test"]) == 1
    assert set(visible["test"][0]) == {"input"}
    assert visible["test"][0]["input"] == episode["test"][2]["input"]
    assert "program_solution" not in visible


def test_invalid_typed_requests_fail_closed():
    module = load_adapter()
    with pytest.raises(ValueError):
        module.generate(True, {"recolor_scope": "all_sources"}, 2, 4)
    with pytest.raises(ValueError):
        module.generate(0, {"recolor_scope": "largest_color"}, 2, 4)
    with pytest.raises(ValueError):
        module.generate(0, {"recolor_scope": "all_sources"}, 1, 4)
    with pytest.raises(ValueError):
        module.generate(0, {"recolor_scope": "all_sources"}, 2, 5)


def test_retained_original_sampler_still_has_four_mapping_stress_profile():
    module=load_adapter()
    old=module._family.old
    pair=old.generate(71,{"recolor_scope":"most_frequent_source"},6,4)["test"][3]
    facts=old.analyze(pair["input"])
    assert facts["n_pairs"]==4
    assert facts["body_nonzero"]>=400


def test_union_preserves_programs_and_teaches_three_choices_at_two_demos():
    module=load_adapter()
    family=module._family
    for mode in family.old.SETTINGS:
        assert module.program({"recolor_scope":mode})==family.old.program({"recolor_scope":mode})
    for seed in (0,17):
        episodes=[module.generate(seed,{"recolor_scope":s},2,4) for s in family.SETTINGS]
        assert len({repr([p["input"] for p in e["train"]+e["test"]]) for e in episodes})==1
        assert len({repr([p["output"] for p in e["train"]]) for e in episodes})==3
