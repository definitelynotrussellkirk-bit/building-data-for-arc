from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "06789067e67f"
ROOT = find_root(__file__)
SOURCE = ROOT / f"generators/{TASK_ID}/workspace/parametric/prototype.py"


def _load():
    assert SOURCE.is_file(), "parametric prototype is missing"
    spec = importlib.util.spec_from_file_location("parametric_06789067e67f_under_test", SOURCE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def proto():
    return _load()


def _canonical_program():
    ledger = ROOT / "shared/data/canonical/puzzles.jsonl"
    for line in ledger.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise AssertionError(TASK_ID)


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_program_contract_preserves_exact_canonical_default(proto):
    assert proto.DEFAULT_SETTINGS == {"output_colors": "original"}
    assert proto.SETTINGS == (
        {"output_colors": "original"},
        {"output_colors": "rank"},
    )
    assert proto.program(proto.DEFAULT_SETTINGS) == _canonical_program()
    assert proto.program({"output_colors": "rank"}) != _canonical_program()


def test_matched_inputs_counts_teaching_and_30x30_stress(proto):
    canonical = proto.generate(17, {"output_colors": "original"}, demos=3, queries=4)
    ranked = proto.generate(17, {"output_colors": "rank"}, demos=3, queries=4)
    assert _inputs(canonical) == _inputs(ranked)
    assert len(canonical["train"]) == len(ranked["train"]) == 3
    assert len(canonical["test"]) == len(ranked["test"]) == 4
    assert canonical["certificate"]["survivors"] == [{"output_colors": "original"}]
    assert ranked["certificate"]["survivors"] == [{"output_colors": "rank"}]
    assert len({proto.digest(grid) for grid in _inputs(canonical)}) == 7
    stress = canonical["test"][3]["input"]
    assert (len(stress), len(stress[0])) == (30, 30)
    profile = proto.analyze_input(stress)
    assert profile["components"] == 4
    assert profile["foreground_cells"] >= 90
    assert profile["row_span"] >= 26
    assert profile["column_span"] >= 26
    assert profile["touches_boundary"]


@pytest.mark.parametrize("demos", [2, 6])
def test_supported_demo_boundaries_keep_exactly_four_queries(proto, demos):
    episode = proto.generate(5, {"output_colors": "rank"}, demos=demos, queries=4)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == 4
    assert episode["certificate"]["survivors"] == [{"output_colors": "rank"}]


def test_query_prefix_is_independent_of_demo_count(proto):
    small = proto.generate(13, {"output_colors": "original"}, demos=2, queries=4)
    large = proto.generate(13, {"output_colors": "original"}, demos=6, queries=4)
    assert small["test"] == large["test"]
    assert proto.public_turn(small, 0)["test"] == proto.public_turn(large, 0)["test"]


def test_rank_setting_is_genuinely_sequential(proto):
    episode = proto.generate(23, {"output_colors": "rank"}, demos=3, queries=4)
    witness = next(pair for pair in episode["test"] if proto.skip_pack_counterfactual(pair["input"]) != pair["output"])
    intermediate = proto.canonical_transform(witness["input"])
    assert proto.rank_recolor(intermediate) == witness["output"]
    assert proto.skip_pack_counterfactual(witness["input"]) != witness["output"]
    assert intermediate != witness["input"]


def test_real_racket_labels_for_both_settings(proto):
    with RacketBridge(timeout=60) as bridge:
        for setting in proto.SETTINGS:
            episode = proto.generate(31, setting, demos=3, queries=4)
            for pair in episode["train"] + episode["test"]:
                assert proto.execute_rule(episode["program_solution"], pair["input"], bridge=bridge) == pair["output"]
            cert = proto.certify(
                episode,
                execute=lambda source, grid: proto.execute_rule(source, grid, bridge=bridge),
            )
            assert cert["survivors"] == [setting]


def test_public_projection_excludes_settings_program_answers_and_future_queries(proto):
    episode = proto.generate(37, {"output_colors": "rank"}, demos=3, queries=4)
    visible = proto.public_turn(episode, 0)
    assert len(visible["test"]) == 1
    assert set(visible["test"][0]) == {"input"}
    before = public_challenge_bytes(visible)
    changed = copy.deepcopy(episode)
    changed["settings"] = {"output_colors": "original"}
    changed["program_solution"] = "private mutation"
    changed["test"][0]["output"] = [[9]]
    changed["test"][1]["input"] = [[9]]
    assert public_challenge_bytes(proto.public_turn(changed, 0)) == before
    assert public_challenge_id(proto.public_turn(changed, 0)) == public_challenge_id(visible)
    visible_change = copy.deepcopy(episode)
    visible_change["train"][0]["output"] = [[9]]
    assert public_challenge_id(proto.public_turn(visible_change, 0)) != public_challenge_id(visible)


@pytest.mark.parametrize(
    "settings,demos,queries",
    [
        ({"output_colors": "rank"}, True, 4),
        ({"output_colors": "rank"}, 1, 4),
        ({"output_colors": "rank"}, 7, 4),
        ({"output_colors": "rank"}, 3, 3),
        ({"output_colors": "position"}, 3, 4),
        ({"output_colors": "rank", "extra": 1}, 3, 4),
    ],
)
def test_invalid_episode_contracts_fail_closed(proto, settings, demos, queries):
    with pytest.raises((TypeError, ValueError)):
        proto.generate(0, settings, demos=demos, queries=queries)


def test_corrupt_labels_duplicate_inputs_and_malformed_grids_are_rejected(proto):
    episode = proto.generate(41, {"output_colors": "rank"}, demos=3, queries=4)
    corrupt = copy.deepcopy(episode)
    corrupt["train"][0]["output"] = [[0]]
    with pytest.raises(ValueError, match="label"):
        proto.certify(corrupt)
    duplicate = copy.deepcopy(episode)
    duplicate["test"][0]["input"] = copy.deepcopy(duplicate["train"][0]["input"])
    with pytest.raises(ValueError, match="distinct"):
        proto.certify(duplicate)
    with pytest.raises(ValueError):
        proto.canonical_transform([[True]])


def test_two_demo_minimum_constructively_refutes_color_only_seed_286(proto):
    for setting in proto.SETTINGS:
        episode = proto.generate(286, setting, demos=2, queries=4)
        expected = [pair["output"] for pair in episode["train"]]
        color_only = [
            proto.rival_transform("color_only", pair["input"], setting)
            for pair in episode["train"]
        ]
        assert color_only != expected


def test_rank_setting_teaches_color_tie_direction_at_two_demos(proto):
    episode = proto.generate(0, {"output_colors": "rank"}, demos=2, queries=4)

    def wrong_color_direction(grid):
        records = sorted(
            proto._components(grid),
            key=lambda record: (-record["holes"], -record["area"], -record["color"]),
        )
        return proto.rank_recolor(proto._packed(records))

    expected = [pair["output"] for pair in episode["train"]]
    wrong = [wrong_color_direction(pair["input"]) for pair in episode["train"]]
    assert wrong != expected


@pytest.mark.parametrize("seed", [0, 7, 17, 41, 91])
def test_two_demo_minimum_refutes_additional_sort_shortcuts(proto, seed):
    names = (
        "wrong_color_tie",
        "wrong_area_tie",
        "area_scan",
        "holes_area_scan",
        "bbox_area",
        "height_only",
        "width_only",
        "source_top",
    )
    for setting in proto.SETTINGS:
        episode = proto.generate(seed, setting, demos=2, queries=4)
        expected = [pair["output"] for pair in episode["train"]]
        for name in names:
            actual = [
                proto.rival_transform(name, pair["input"], setting)
                for pair in episode["train"]
            ]
            assert actual != expected, (seed, setting, name)


def _load_neighbor(filename, module_name):
    path = SOURCE.with_name(filename)
    assert path.is_file(), f"missing reusable authoring tool: {filename}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_semantic_sweep_tool_reports_no_minimum_lesson_survivors():
    sweep = _load_neighbor("semantic_sweep.py", "semantic_sweep_06789067e67f")
    report = sweep.build_report(seed_count=16)
    assert report["status"] == "passed"
    assert report["seed_count"] == 16
    assert report["rival_count"] >= 18
    assert report["survivor_count"] == 0
    assert report["ambiguous_count"] == 0


def test_protected_probe_candidate_bank_covers_sort_pack_and_rank_bypasses(proto):
    probe = _load_neighbor("adversarial_probe.py", "adversarial_probe_06789067e67f")
    banks = probe.candidate_sources(proto)
    assert set(banks) == {"original", "rank"}
    assert len(banks["original"]) >= 16
    assert len(banks["rank"]) >= 20
    required = {
        "color_only",
        "wrong_color_tie",
        "gap0",
        "bottom_align",
        "filled_bbox",
        "skip_pack_rank",
        "reverse_rank",
        "color_rank",
        "partial_rank_first",
    }
    assert required <= set(banks["original"]) | set(banks["rank"])


def test_two_demo_minimum_refutes_holes_only_with_scan_order_ties(proto):
    for setting in proto.SETTINGS:
        episode = proto.generate(0, setting, demos=2, queries=4)

        def holes_scan(grid):
            records = sorted(proto._components(grid), key=lambda record: -record["holes"])
            intermediate = proto._packed(records)
            return (
                intermediate
                if setting["output_colors"] == "original"
                else proto.rank_recolor(intermediate)
            )

        wrong = [holes_scan(pair["input"]) for pair in episode["train"]]
        expected = [pair["output"] for pair in episode["train"]]
        assert wrong != expected


def test_skip_pack_counterfactual_racket_matches_python(proto):
    source_path = SOURCE.with_name("skip_pack.rkt")
    assert source_path.is_file(), "missing protected-Racket causal counterfactual"
    source = source_path.read_text()
    episode = proto.generate(23, {"output_colors": "rank"}, demos=2, queries=4)
    with RacketBridge(timeout=60) as bridge:
        for pair in episode["test"]:
            assert proto.execute_rule(source, pair["input"], bridge=bridge) == proto.skip_pack_counterfactual(pair["input"])
