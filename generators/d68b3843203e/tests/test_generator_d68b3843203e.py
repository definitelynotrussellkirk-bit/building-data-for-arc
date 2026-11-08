"""Task-local regressions. Run from the repo with python -m pytest <this-file>."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import random
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
sys.path.insert(0, str(REPO / "shared/runtime"))
SPEC = importlib.util.spec_from_file_location("reviewed_d68b3843203e", HOME / "generator.py")
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def canonical_task():
    with (REPO / "shared/data/canonical/puzzles.jsonl").open() as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("task_id") == "d68b3843203e":
                return row
    raise AssertionError("canonical task d68b3843203e not found")


def canonical_pairs():
    row = canonical_task()
    return row["train"] + row["test"]


def scan_frames(grid):
    """Independent exhaustive border scan (not the generator's component parser)."""
    h, w = len(grid), len(grid[0])
    frames = []
    for r0 in range(h - 2):
        for c0 in range(w - 2):
            if grid[r0][c0] != 4:
                continue
            for r1 in range(r0 + 2, h):
                for c1 in range(c0 + 2, w):
                    border = {(r, c) for r in range(r0, r1 + 1)
                              for c in range(c0, c1 + 1)
                              if r in (r0, r1) or c in (c0, c1)}
                    if not all(grid[r][c] == 4 for r, c in border):
                        continue
                    if any(grid[nr][nc] == 4 and (nr, nc) not in border
                           for r, c in border for nr, nc in
                           ((r-1,c),(r+1,c),(r,c-1),(r,c+1))
                           if 0 <= nr < h and 0 <= nc < w):
                        continue
                    cells = [(r, c) for r in range(r0 + 1, r1)
                             for c in range(c0 + 1, c1)]
                    frames.append((r0, c0, r1, c1, cells,
                                   sum(grid[r][c] == 2 for r,c in cells)))
    return frames


def expected_output(grid):
    out = copy.deepcopy(grid)
    for *_, cells, count in scan_frames(grid):
        for r, c in cells:
            out[r][c] = 5 + count
    return out


def test_rule_hash_pin():
    assert getattr(GEN, "RULE_HASH", None) == "90de3c06fb83"


def test_all_canonical_inputs_accepted():
    for pair in canonical_pairs():
        assert GEN.self_check(pair["input"]) == []


def test_canonical_mirror():
    assert hasattr(GEN, "rule_mirror"), "missing independently Racket-checked Python mirror"
    for pair in canonical_pairs():
        before = copy.deepcopy(pair["input"])
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert GEN.rule_mirror(pair["input"]) == expected_output(pair["input"])
        assert pair["input"] == before


def test_unknown_override_is_not_silently_ignored():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(17, 0, typo_axis=42)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("h,w,n", [(8,8,2),(8,8,3),(16,18,2),(16,18,3)])
def test_declared_boundaries_all_bands(band, h, w, n):
    grid = GEN.generate(3, 1, difficulty=band, grid_h=h, grid_w=w, n_frames=n)
    assert (len(grid), len(grid[0])) == (h, w)
    assert len(scan_frames(grid)) == n
    assert GEN.self_check(grid) == []


@pytest.mark.parametrize("value", [0,1,4,-1,True,2.5,"2"])
def test_invalid_frame_counts_rejected(value):
    with pytest.raises(ValueError):
        GEN.generate(1, 0, n_frames=value)


def test_realized_axis_observer():
    assert hasattr(GEN, "observe_overrides"), "exact axes need realized-value observations"
    for cue_size in (1,2):
        grid = GEN.generate(9, 0, grid_h=12, grid_w=14, n_frames=3, cue_size=cue_size)
        assert GEN.observe_overrides(grid) == {
            "grid_h":12, "grid_w":14, "n_frames":3, "cue_size":cue_size,
        }


def test_default_geometry_and_count_diversity():
    shapes, numbers = set(), set()
    repeated = adjacent_pair = separated_three = False
    for i in range(120):
        grid = GEN.generate(811, i)
        frames = scan_frames(grid)
        shapes.update((r1-r0+1,c1-c0+1) for r0,c0,r1,c1,_,_ in frames)
        numbers.add(len(frames))
        counts = [f[-1] for f in frames]
        repeated |= len(set(counts)) < len(counts)
        for *_, cells, count in frames:
            markers = {(r,c) for r,c in cells if grid[r][c] == 2}
            touching = any((r+1,c) in markers or (r,c+1) in markers for r,c in markers)
            adjacent_pair |= count == 2 and touching
            separated_three |= count == 3 and not touching
    assert numbers == {2,3}
    assert any(3 in shape for shape in shapes)
    assert len(shapes) >= 8
    assert repeated and adjacent_pair and separated_three


def test_validator_rejects_extra_markers_and_merged_yellow_components():
    grid = canonical_pairs()[0]["input"]
    extra = copy.deepcopy(grid)
    extra[0][0] = 2
    assert GEN.self_check(extra), "outside marker accepted"
    spur = copy.deepcopy(grid)
    spur[0][1] = 4
    assert GEN.self_check(spur), "non-rectangular yellow component accepted"
    overfull = copy.deepcopy(grid)
    for r,c in [(2,2),(2,3),(3,2),(3,3)]:
        overfull[r][c] = 2
    assert GEN.self_check(overfull), "frame with four markers accepted"


@pytest.mark.parametrize("grid", [None, [], [[]], [[0],[0,1]], [[False]], [[10]], [[0.5]]])
def test_malformed_grids_report_reasons(grid):
    assert GEN.self_check(grid)


def test_seed_determinism_and_global_rng_purity():
    random.seed(9081)
    state = random.getstate()
    grid = GEN.generate(4242, 7, difficulty="hard")
    assert GEN.generate(4242, 7, difficulty="hard") == grid
    assert random.getstate() == state


def test_topology_shortcut_fits_canonical_but_is_refuted_by_generator():
    assert hasattr(GEN, "CANONICAL_SHORTCUTS"), "missing executable shortcut challenge"
    rival = GEN.CANONICAL_SHORTCUTS["marker_topology"]
    assert all(rival(p["input"]) == p["output"] for p in canonical_pairs())
    assert any(rival(g) != expected_output(g)
               for g in (GEN.generate(811,i) for i in range(60)))


def test_broken_frame_rejected():
    grid = copy.deepcopy(canonical_pairs()[0]["input"])
    grid[1][2] = 0
    assert GEN.self_check(grid)


def test_strict_defect_sample_introduces_canonical_color_8_in_a_majority():
    introduced = 0
    for seed in range(1, 21):
        grid = GEN.generate(seed, seed, difficulty="medium")
        output = expected_output(grid)
        introduced += 8 not in {value for row in grid for value in row} and any(
            8 in row for row in output
        )
    assert introduced > 10, (
        "the strict defect-lint sample must teach color 8 as a transformation, "
        "not let cue-color overlap hide it in half the lessons"
    )


def test_default_census_retains_canonical_scale_and_three_marker_examples():
    in_envelope = with_three = repeated = 0
    for i in range(120):
        grid = GEN.generate(811,i)
        frames = scan_frames(grid)
        counts = [f[-1] for f in frames]
        in_envelope += 10 <= len(grid) <= 12 and 11 <= len(grid[0]) <= 13
        with_three += 3 in counts
        repeated += len(set(counts)) < len(counts)
    assert in_envelope >= 36, "broad dimensions swamped canonical-scale teaching"
    assert with_three >= 72, "three-marker / color-8 lessons underrepresented"
    assert repeated >= 8, "coverage must not force all frame counts to differ"


def test_edge_and_interior_layouts_both_have_material_support():
    no_edge = 0
    for i in range(120):
        grid = GEN.generate(811,i)
        no_edge += all(r0 > 0 and c0 > 0 and r1 < len(grid)-1 and c1 < len(grid[0])-1
                       for r0,c0,r1,c1,_,_ in scan_frames(grid))
    assert 12 <= no_edge <= 108, "layout should not always force or avoid edge contact"



def test_default_profile_weights_canonical_marginals_without_copying_joint():
    profiles = []
    for i in range(400):
        grid = GEN.generate(12345, i)
        observed = GEN.observe_overrides(grid)
        profiles.append((observed["n_frames"], observed["cue_size"]))
    three_frames = sum(n == 3 for n, _ in profiles)
    single_cue = sum(cue == 1 for _, cue in profiles)
    assert 260 <= three_frames <= 380, "canonical-majority three-frame scenes lost"
    assert 260 <= single_cue <= 380, "canonical-majority one-cell cues lost"
    assert set(profiles) == {(2, 1), (2, 2), (3, 1), (3, 2)},         "marginal weighting must not copy the canonical n_frames/cue_size correlation"


def test_selected_rule_is_lint_clean_hash_pinned_and_source_synchronized():
    rule = canonical_task()["program_solution"]
    assert "(let ((dummy 0))" not in rule, "selected rule retains dummy-let lint finding"
    expected_hash = hashlib.sha256(" ".join(rule.split()).encode()).hexdigest()[:12]
    assert GEN.RULE_HASH == expected_hash
    base = json.loads((REPO / "shared/data/base/solutions/banks/385e738e9e70/"
                       "M93__d68b3843203e.json").read_text())
    assert base["racket_target"]["target_code"] == rule
