from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1]
PARAMETRIC = HERE / "workspace" / "parametric"
SPEC = importlib.util.spec_from_file_location("native_adapter_d377", PARAMETRIC / "adapter.py")
ADAPTER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(ADAPTER)

GEN_SPEC = importlib.util.spec_from_file_location("generator_d377_for_adapter_test", HERE / "generator.py")
GENERATOR = importlib.util.module_from_spec(GEN_SPEC)
assert GEN_SPEC.loader is not None
GEN_SPEC.loader.exec_module(GENERATOR)


def test_default_program_is_byte_exact_canonical_authority():
    canonical = (PARAMETRIC / "rules" / "canonical.rkt").read_text(encoding="utf-8")
    assert ADAPTER.canonical_program() == canonical
    assert ADAPTER.program({"finish": "redraw_only"}) == canonical


def test_generate_has_native_limits_prefix_stability_and_matched_inputs():
    default = ADAPTER.generate(17, {"finish": "redraw_only"}, 6, 4)
    alternate = ADAPTER.generate(17, {"finish": "highlight_most_stroke_cells"}, 6, 4)
    assert len(default["train"]) == len(alternate["train"]) == 6
    assert len(default["test"]) == len(alternate["test"]) == 4
    assert [p["input"] for p in default["train"] + default["test"]] == [
        p["input"] for p in alternate["train"] + alternate["test"]
    ]
    small = ADAPTER.generate(17, {"finish": "redraw_only"}, 2, 1)
    assert small["train"] == default["train"][:2]
    assert small["test"] == default["test"][:1]
    assert any(len(p["input"]) == len(p["input"][0]) == 30 for p in default["test"])
    assert len({str(p["input"]) for p in default["train"] + default["test"]}) == 10


def test_canonical_python_labels_match_production_mirror_on_all_banked_inputs():
    for seed in (0, 17, 97):
        episode = ADAPTER.generate(seed, {"finish": "redraw_only"}, 6, 4)
        for pair in episode["train"] + episode["test"]:
            assert pair["output"] == GENERATOR.rule_mirror(pair["input"])


def test_two_demonstrations_identify_each_setting_against_declared_rivals():
    for seed in (0, 17, 97):
        for finish in ADAPTER.SETTINGS:
            episode = ADAPTER.generate(seed, {"finish": finish}, 2, 4)
            certificate = ADAPTER.certificate(episode["train"], [p["input"] for p in episode["test"]])
            assert certificate["survivors"] == [finish]
            assert set(certificate["query_disagreements"]) == set(ADAPTER.HYPOTHESES) - {finish}


def test_sequential_intermediate_selects_neither_metric_proxy_nor_input_marker_proxy():
    episode = ADAPTER.generate(23, {"finish": "highlight_most_stroke_cells"}, 2, 4)
    for pair in episode["train"] + episode["test"]:
        info = ADAPTER.observe(pair["input"])
        target = info["stroke_winner"]
        assert info["stroke_winner_count"] == 1
        assert target != info["largest_area"]
        assert target != info["largest_perimeter"]
        assert target != info["tallest"]
        assert target != info["widest"]
        assert target != info["most_input_markers"]
        assert target != info["fewest_input_markers"]
        assert target != info["first_object"]
        assert target != info["last_object"]
        assert target != info["highest_marker_color"]
        assert target != info["lowest_marker_color"]
        assert ADAPTER.predict(pair["input"], "highlight_most_input_markers") != pair["output"]


def test_alternate_changes_only_the_selected_post_redraw_stroke_cells():
    episode = ADAPTER.generate(5, {"finish": "highlight_most_stroke_cells"}, 2, 1)
    source = episode["train"][0]["input"]
    base = ADAPTER.predict(source, "redraw_only")
    alternate = ADAPTER.predict(source, "highlight_most_stroke_cells")
    info = ADAPTER.observe(source)
    selected = next(record for record in info["records"] if record["index"] == info["stroke_winner"])
    expected_changed = set(selected["stroke_cells"])
    changed = {(r, c) for r, row in enumerate(base) for c, value in enumerate(row) if value != alternate[r][c]}
    assert changed == expected_changed
    assert changed
    assert all(alternate[r][c] == 9 for r, c in changed)


@pytest.mark.parametrize("bad", [True, 1.0, "1", -1])
def test_seed_requires_nonnegative_exact_integer(bad):
    with pytest.raises(ValueError):
        ADAPTER.generate(bad, {"finish": "redraw_only"}, 2, 1)


@pytest.mark.parametrize("settings", [{}, {"finish": "unknown"}, {"finish": "redraw_only", "x": 1}, None])
def test_settings_fail_closed(settings):
    with pytest.raises(ValueError):
        ADAPTER.generate(0, settings, 2, 1)


@pytest.mark.parametrize("demos,queries", [(1, 1), (7, 1), (2, 0), (2, 5), (True, 1), (2, True)])
def test_count_limits_fail_closed(demos, queries):
    with pytest.raises(ValueError):
        ADAPTER.generate(0, {"finish": "redraw_only"}, demos, queries)
