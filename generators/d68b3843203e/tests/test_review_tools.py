"""Regression coverage for the portable reviewer tools, not production labeling."""
from pathlib import Path
import sys
import pytest
WORKSPACE = Path(__file__).resolve().parents[1] / "workspace"
sys.path.insert(0, str(WORKSPACE))
import review_probe

@pytest.mark.parametrize("stored", [
    ["012", "340"], [[0,1,2],[3,4,0]], [(0,1,2),(3,4,0)]
])
def test_normalize_storage_to_literal_arc_grid(stored):
    assert review_probe.normalize_grid(stored) == [[0,1,2],[3,4,0]]

@pytest.mark.parametrize("stored", [[], [""], ["00","0"], ["0x"], [[True]], [[10]], [[0.0]]])
def test_normalizer_rejects_malformed_or_nonliteral_cells(stored):
    with pytest.raises(ValueError):
        review_probe.normalize_grid(stored)

def test_mixed_canonical_storage_is_normalized_before_rule_replay():
    task = review_probe.read_task("edb55a59dc46")
    assert task["train"][0]["input"][0] == [0,2,8,0,0,0,0,0,0]


def test_scene_profile_counts_frames_and_exterior_cue_cells():
    task = review_probe.read_task("d68b3843203e")
    assert review_probe.scene_profile(task["train"][2]["input"]) == (2, 2)
    assert review_probe.scene_profile(task["train"][0]["input"]) == (3, 1)

import audit_probe


def test_audit_probe_tracks_current_assignment_targets():
    assert audit_probe.IDS == ("4a3ababcaceb", "cf60523d1603")


def test_largest_motif_shortcut_differs_on_accepted_decoy_counterexample():
    rival = audit_probe.largest_motif_rival(audit_probe.TILE_ADVERSARY)
    assert rival[1][5] == 8  # densest color-1 decoy paints target center
    assert audit_probe.TILE_EXPECTED[1][5] == 0  # color-2 authority leaves it blank


def test_endpoint_presence_shortcut_differs_on_mixed_color_counterexample():
    rival = audit_probe.endpoint_presence_rival(audit_probe.COLUMN_ADVERSARY)
    assert rival[1][2] == 3  # shortcut bridges mismatched 3/4 endpoints
    assert audit_probe.COLUMN_EXPECTED[1][2] == 0


def test_single_test_pair_dict_is_normalized_to_pair_list():
    task = review_probe.read_task("4a3ababcaceb")
    assert isinstance(task["test"], list)
    assert len(task["test"]) == 1
    assert task["test"][0]["input"][0] == [0, 1, 0, 9, 2, 2, 0, 9, 0, 0, 0]
