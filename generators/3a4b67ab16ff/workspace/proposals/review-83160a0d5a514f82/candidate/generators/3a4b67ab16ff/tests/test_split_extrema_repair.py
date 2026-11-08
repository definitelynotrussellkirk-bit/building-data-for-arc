"""Focused regression tests for the split-extrema curriculum repair."""
from __future__ import annotations

import hashlib

import pytest
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "3a4b67ab16ff"
ROOT = find_root(__file__)
MODULE = load_selected_generator(TASK_ID, root=ROOT)[0]
BANDS = ("easy", "medium", "hard")


def _endpoint_only_rule(grid):
    """Known shortcut: use only first/last row-major marker occurrences."""
    facts = MODULE._extract_facts(grid)
    output = [[0 for _ in row] for row in grid]
    for row, col in facts["gray_area"]:
        output[row][col] = 5
    for color in sorted(facts["colors"]):
        cells = facts["colors"][color]["cells"]
        endpoint_bbox = MODULE._bbox((cells[0], cells[-1]))
        intersection = MODULE._intersection(endpoint_bbox, facts["gray_bbox"])
        for row, col in MODULE._rect_cells(intersection):
            output[row][col] = color
    return output


def _profile(grid):
    return (len(grid), len(grid[0]), len({cell for row in grid for cell in row}))


def _pinned_seed(band: str, index: int) -> int:
    digest = hashlib.sha256(
        f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode("utf-8")
    ).hexdigest()
    return int(digest[:12], 16)


def test_split_extrema_profile_is_recoverable_in_every_band():
    for band_index, band in enumerate((None, *BANDS)):
        for seed in range(20):
            grid = MODULE.generate(
                900_000 + band_index * 1_000 + seed,
                seed * 41,
                difficulty=band,
                scene_profile="split_extrema",
            )
            analysis = MODULE._analysis(grid)
            assert not analysis["errors"]
            assert analysis["scene_profile"] == "split_extrema"
            assert MODULE.observe_overrides(grid) == {"scene_profile": "split_extrema"}


def test_split_extrema_profile_refutes_first_last_occurrence_bbox_rival():
    for seed in range(40):
        grid = MODULE.generate(
            910_000 + seed,
            seed * 43,
            scene_profile="split_extrema",
        )
        facts = MODULE._analysis(grid)["facts"]
        color, = facts["active_colors"]
        cells = facts["colors"][color]["cells"]
        true_bbox = facts["colors"][color]["bbox"]
        endpoint_bbox = MODULE._bbox((cells[0], cells[-1]))
        row0, col0, row1, col1 = true_bbox
        assert endpoint_bbox != true_bbox
        assert (row0, col0) not in cells
        assert (row1, col1) not in cells
        assert _endpoint_only_rule(grid) != MODULE.rule_mirror(grid)


def test_pinned_default_schedule_retains_canonical_profile_support_per_band():
    canonical = canonical_pairs(TASK_ID, root=ROOT, labeled_only=False)
    profiles = {_profile(pair["input"]) for pair in canonical}
    h_values = [profile[0] for profile in profiles]
    w_values = [profile[1] for profile in profiles]
    p_values = [profile[2] for profile in profiles]
    envelope = (
        (min(h_values), max(h_values)),
        (min(w_values), max(w_values)),
        (min(p_values), max(p_values)),
    )

    exact_by_band = {}
    exact_total = 0
    envelope_total = 0
    for band in BANDS:
        exact = 0
        inside = 0
        for index in range(20):
            seed = _pinned_seed(band, index)
            sample_index = seed % 7919 + index
            profile = _profile(MODULE.generate(seed, sample_index, difficulty=band))
            exact += profile in profiles
            (h0, h1), (w0, w1), (p0, p1) = envelope
            inside += h0 <= profile[0] <= h1 and w0 <= profile[1] <= w1 and p0 <= profile[2] <= p1
        exact_by_band[band] = exact
        exact_total += exact
        envelope_total += inside

    assert all(count >= 1 for count in exact_by_band.values()), exact_by_band
    assert exact_total >= 3
    assert envelope_total >= 15


def test_semantic_contract_names_and_refutes_the_endpoint_only_rival():
    witness_name = "split_extrema_refutes_endpoint_only_bbox"
    rival_name = "endpoint_only_bbox"
    assert set(MODULE.SEMANTIC_WITNESSES) == {witness_name}
    assert set(MODULE.SEMANTIC_RIVALS) == {rival_name}
    assert MODULE.WITNESS_RIVALS == {witness_name: [rival_name]}

    rival = MODULE.SEMANTIC_RIVALS[rival_name]
    witness = MODULE.SEMANTIC_WITNESSES[witness_name]
    canonical = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert all(rival(pair["input"]) == pair["output"] for pair in canonical)

    for seed in range(12):
        grid = MODULE.generate(
            920_000 + seed,
            seed * 47,
            scene_profile="split_extrema",
        )
        assert witness(grid)
        assert rival(grid) != MODULE.rule_mirror(grid)


@pytest.mark.parametrize("bad", [True, False, 1.0, 1.75, "1", None])
def test_generate_rejects_non_integer_seed_and_sample_index(bad):
    with pytest.raises(TypeError):
        MODULE.generate(bad, 0)
    with pytest.raises(TypeError):
        MODULE.generate(0, bad)


def test_generate_rejects_negative_sample_index():
    with pytest.raises(ValueError):
        MODULE.generate(0, -1)
