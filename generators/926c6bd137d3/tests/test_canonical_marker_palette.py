from itertools import combinations
from reviewer_support import find_root, load_selected_generator, canonical_pairs

ROOT = find_root(__file__)
GEN, SOURCE, SHA = load_selected_generator("926c6bd137d3", root=ROOT)
CANONICAL_COLORS = {1, 2, 3, 6, 8}

def palette_restricted_rival(grid):
    output = [row[:] for row in grid]
    info, errors = GEN._analyse(grid)
    assert not errors
    for frame, marker_color in zip(info["frames"], info["marker_colors"]):
        if marker_color in CANONICAL_COLORS:
            for r in range(frame[0]+1, frame[2]):
                for c in range(frame[1]+1, frame[3]):
                    if output[r][c] == 0:
                        output[r][c] = marker_color
    return output

def lesson(seed, start, band):
    pairs = []
    for i in range(start, start+5):
        grid = GEN.generate(seed, i, difficulty=band)
        pairs.append({"input":grid,"output":GEN.rule_mirror(grid)})
    return pairs

def test_indices_three_to_seven_demonstrate_novel_marker_semantics():
    pairs = lesson(0, 3, "easy")
    assert any(palette_restricted_rival(p["input"]) != p["output"] for p in pairs[:4]), \
        "canonical-only palette rival fits every demo in seed0 indices3..6"

def test_novel_marker_control_survives_every_query_holdout():
    for seed in (0, 1, 7):
        for band in (None, "easy", "medium", "hard"):
            for start in range(8):
                pairs = lesson(seed, start, band)
                assert all(GEN.self_check(p["input"]) == [] for p in pairs)
                for qi in range(5):
                    demos = pairs[:qi] + pairs[qi+1:]
                    assert any(palette_restricted_rival(p["input"]) != p["output"] for p in demos)
                    assert GEN.lesson_identifiable(demos, pairs[qi]) == []

def test_canonical_palette_rival_is_truthfully_declared():
    rival = GEN.CANONICAL_SHORTCUTS["canonical_marker_palette"]
    pairs = canonical_pairs("926c6bd137d3", root=ROOT, labeled_only=True)
    assert len(pairs) == 5
    assert all(rival(p["input"]) == p["output"] for p in pairs)

def test_marker_assignment_preserves_exact_controls_with_added_rival():
    for frames in (1,2,3,4):
        grid = GEN.generate(17, 2, grid_h=10, grid_w=18, n_frames=frames, n_exterior_distractors=4)
        assert GEN.observe_overrides(grid) == {"grid_h":10,"grid_w":18,"n_frames":frames,"n_exterior_distractors":4}
        assert GEN.generation_check(grid) == []
