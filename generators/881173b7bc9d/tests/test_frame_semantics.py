"""Independent literal Racket fixtures for the frame detector and packer.

These test the raw reference behavior. In particular, a no-frame reference
fixture need not belong to the generator's narrower validated support.
"""
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root


TASK = "881173b7bc9d"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK
FIXTURE_PATH = HOME / "counterexamples" / "frame_semantics.json"
FIXTURES = json.loads(FIXTURE_PATH.read_text())
SPEC = importlib.util.spec_from_file_location("independent_frame_semantics", HOME / "generator.py")
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def test_saved_labels_are_bound_to_unchanged_authority():
    authority = FIXTURES["authority"]
    source = ROOT / authority["path"]
    assert hashlib.sha256(source.read_bytes()).hexdigest() == authority["sha256"]
    rule = json.loads(source.read_text())["racket_target"]["target_code"]
    assert hashlib.sha256(rule.encode()).hexdigest() == authority["rule_text_sha256"]
    assert authority["executed_rule_hash"] == "b87fde7ab095"


@pytest.mark.parametrize("case", FIXTURES["witnesses"], ids=lambda case: case["name"])
def test_detector_and_packer_match_literal_racket_counterexamples(case):
    grid = case["input"]
    assert GEN._pack(grid, GEN._frames(grid)) == case["racket_output"]
    assert case["rival_prediction"] != case["racket_output"]


@pytest.mark.parametrize("case", FIXTURES["authority_endpoints"], ids=lambda case: case["name"])
def test_raw_reference_endpoints(case):
    grid = case["input"]
    assert GEN._pack(grid, GEN._frames(grid)) == case["racket_output"]


@pytest.mark.parametrize("case", FIXTURES["canonical"],
                         ids=lambda case: f"v{case['variant']}-{case['split']}-{case['pair_index']}")
def test_every_canonical_output_with_portable_data_and_literal_fixture(case):
    pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    selected = [p for p in pairs if (p["variant"], p["split"], p["pair_index"]) ==
                (case["variant"], case["split"], case["pair_index"])]
    assert len(selected) == 1
    assert selected[0]["input"] == case["input"]
    assert selected[0]["output"] == case["output"]
    digest = hashlib.sha256(json.dumps({"input":case["input"], "output":case["output"]},
                                      sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    assert digest == case["pair_sha256"]
    assert GEN._pack(case["input"], GEN._frames(case["input"])) == case["output"]


@pytest.mark.parametrize("name,options,expected_count", [
    ("global_color", {"group_by_color": True}, 2),
    ("eight_connected", {"connectivity": 8}, 1),
])
def test_component_modes_separate_reference_from_canonical_fit_rivals(name, options, expected_count):
    case = next(w for w in FIXTURES["witnesses"] if w["name"] == name)
    grid = case["input"]
    assert len(GEN._frames(grid)) == expected_count
    assert GEN._pack(grid, GEN._frames(grid, **options)) == case["rival_prediction"]


def test_retained_canonical_fit_statistics_cover_seven_rivals_and_four_labels():
    stats = FIXTURES["canonical_rival_fit_stats"]
    assert set(stats) == {"global_color", "eight_connected", "right_edge", "center",
                          "min_four", "perimeter_count_only", "ninety_percent_complete"}
    assert len(FIXTURES["canonical"]) == 4
    assert all(row == {"labeled_pairs":4, "matches":4, "fits_all":True}
               for row in stats.values())
