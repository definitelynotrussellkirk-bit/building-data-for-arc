from pathlib import Path
import pytest
from reviewer_support import find_root, load_selected_generator, canonical_pairs

ROOT = find_root(__file__)
G, SOURCE, SOURCE_HASH = load_selected_generator("d377a54f20c6", root=ROOT)

@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1"])
def test_seed_requires_an_actual_integer(seed):
    with pytest.raises(ValueError):
        G.generate(seed, 0)

@pytest.mark.parametrize("index", [True, False, 1.0, 1.75, "1", -1])
def test_sample_index_requires_a_nonnegative_actual_integer(index):
    with pytest.raises(ValueError):
        G.generate(7, index)

def test_canonical_pairs_remain_exact_and_singleton_shortcut_is_real():
    for pair in canonical_pairs("d377a54f20c6", root=ROOT):
        assert G.rule_mirror(pair["input"]) == pair["output"]
        assert G.CANONICAL_SHORTCUTS["singleton_marker_required"](pair["input"]) == pair["output"]

def test_rich_examples_refute_all_declared_rivals():
    for band in ("easy", "medium", "hard"):
        for seed in range(5):
            for index in range(0, 16, 2):
                grid = G.generate(seed, index, difficulty=band)
                assert G.self_check(grid) == []
                truth = G.rule_mirror(grid)
                for name, rival in G.LESSON_COMPETITORS.items():
                    assert rival(grid) != truth, (band, seed, index, name)

def test_every_schedule_window_and_rotation_is_identified_without_query_labels():
    for band in ("easy", "medium", "hard"):
        for seed in range(4):
            for start in range(G.LESSON_SCHEDULE_PERIOD):
                pairs = []
                for index in range(start, start + G.EXAMPLES_NEEDED + 1):
                    grid = G.generate(seed, index, difficulty=band)
                    pairs.append({"input": grid, "output": G.rule_mirror(grid)})
                for held_out, query in enumerate(pairs):
                    demos = [p for i,p in enumerate(pairs) if i != held_out]
                    assert G.lesson_identifiable(demos, {"input": query["input"], "output": [[9]]}) == []
                    for name, rival in G.LESSON_COMPETITORS.items():
                        assert any(rival(p["input"]) != p["output"] for p in demos), (band,seed,start,held_out,name)

def test_semantic_witness_claims_have_real_counterexamples():
    for profile in G.GENERAL_PROFILES:
        grid = G.generate(17, 21, scene_profile=profile)
        truth = G.rule_mirror(grid)
        for name, predicate in G.SEMANTIC_WITNESSES.items():
            if predicate(grid):
                assert any(G.SEMANTIC_RIVALS[r](grid) != truth for r in G.WITNESS_RIVALS[name])


def test_lesson_hook_rejects_the_reproduced_singleton_shortcut():
    demos = [{"input": grid, "output": G.rule_mirror(grid)}
             for grid in list(G._PUBLIC_INPUTS.values())[:3]]
    query = G.generate(1, 3, difficulty="medium", scene_profile="multiple_marker_pixels")
    reasons = G.lesson_identifiable(demos, {"input": query, "output": [[9]]})
    assert any("singleton_marker_required" in reason for reason in reasons)
