"""Replay searched spatial rivals as actual input-only hypotheses."""
from __future__ import annotations

import copy
import importlib.util

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "72f0b65569a4"
ROOT = find_root(__file__)
PROBE_PATH = ROOT / "generators" / TASK_ID / "workspace/mirror_contract_probe.py"
SPEC = importlib.util.spec_from_file_location("nearest_object_probe_for_tests", PROBE_PATH)
assert SPEC is not None and SPEC.loader is not None
PROBE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROBE)

RECIPES = (
    ("medium", 40773458261703, 22),
    ("medium", 109628012465557, 33),
    ("hard", 32447781138309, 0),
    ("hard", 155788352441497, 33),
)


@pytest.fixture(scope="module")
def labeled():
    """One public Catalog batch labels all four original warning windows."""
    from arcpuzzles import Catalog

    gen, _source, digest = load_selected_generator(TASK_ID, root=ROOT)
    assert gen.EXAMPLES_NEEDED == 3
    records = {}
    for band, seed, start in RECIPES:
        for si in range(start, start + 4):
            records[(band, seed, si)] = {"input": gen.generate(seed, si, difficulty=band)}
    for index, pair in enumerate(canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)):
        records[("canonical", index)] = pair
    result = Catalog(ROOT).apply(TASK_ID, [pair["input"] for pair in records.values()], timeout=120)
    assert result["generator_sha256"] == digest
    assert result["rule_hash_matches_catalog"]
    for key, row in zip(records, result["results"], strict=True):
        assert row["error"] is None, (key, row["error"])
        if key[0] == "canonical":
            assert records[key]["output"] == row["output"]
        records[key]["output"] = row["output"]
    return records


@pytest.mark.parametrize("band,seed,start", RECIPES)
def test_all_four_query_rotations_refute_input_only_nearest_frame_rivals(labeled, band, seed, start):
    pairs = [labeled[(band, seed, si)] for si in range(start, start + 4)]
    for ties in (True, False):
        predictions = [PROBE.nearest_frame_only(copy.deepcopy(pair["input"]), frame_wins_ties=ties) for pair in pairs]
        for query_position, query in enumerate(pairs):
            fits_demos = all(predictions[i] == pair["output"] for i, pair in enumerate(pairs) if i != query_position)
            assert not fits_demos or predictions[query_position] == query["output"], {
                "difficulty": band, "seed": seed, "start": start,
                "query_position": query_position, "frame_wins_ties": ties,
            }


@pytest.mark.parametrize("band,seed,start", RECIPES)
def test_both_ordinary_axis_draws_supply_nearest_yellow_counterexamples(labeled, band, seed, start):
    axis_indices = [si for si in range(start, start + 4) if si % 2]
    assert len(axis_indices) == 2
    for si in axis_indices:
        pair = labeled[(band, seed, si)]
        for ties in (True, False):
            assert PROBE.nearest_frame_only(copy.deepcopy(pair["input"]), frame_wins_ties=ties) != pair["output"], {
                "difficulty": band, "seed": seed, "sample_index": si,
                "frame_wins_ties": ties,
            }


def test_only_frame_tie_variant_matches_every_canonical_pair(labeled):
    pairs = [pair for key, pair in labeled.items() if key[0] == "canonical"]
    assert len(pairs) == 3
    assert all(PROBE.nearest_frame_only(pair["input"], frame_wins_ties=True) == pair["output"] for pair in pairs)
    assert any(PROBE.nearest_frame_only(pair["input"], frame_wins_ties=False) != pair["output"] for pair in pairs)
