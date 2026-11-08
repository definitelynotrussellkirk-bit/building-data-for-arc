from __future__ import annotations

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "3a4b67ab16ff"
ROOT = find_root(__file__)
MODULE, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def test_distributed_extrema_profile_defeats_row_major_endpoint_bbox_shortcut():
    assert SOURCE_PATH == ROOT / "generators" / TASK_ID / "generator.py"
    assert len(SOURCE_SHA256) == 64
    assert "distributed_extrema" in MODULE.GENERAL_PROFILES
    for band_index, band in enumerate((None, "easy", "medium", "hard")):
        for seed in range(20):
            grid = MODULE.generate(
                900_000 + band_index * 1_000 + seed,
                seed * 43,
                difficulty=band,
                scene_profile="distributed_extrema",
            )
            analysis = MODULE._analysis(grid)
            assert not analysis["errors"]
            assert analysis["scene_profile"] == "distributed_extrema"
            facts = analysis["facts"]
            assert len(facts["active_colors"]) == 1
            color = facts["active_colors"][0]
            cells = facts["colors"][color]["cells"]
            true_bbox = facts["colors"][color]["bbox"]
            endpoint_bbox = MODULE._bbox((min(cells), max(cells)))
            assert endpoint_bbox != true_bbox
            row0, col0, row1, col1 = true_bbox
            corners = {(row0, col0), (row0, col1), (row1, col0), (row1, col1)}
            assert not corners.intersection(cells)
            assert {row for row, _ in cells} >= {row0, row1}
            assert {col for _, col in cells} >= {col0, col1}


def test_default_sampler_keeps_a_canonical_profile_anchor_in_each_band():
    import hashlib

    profiles = {
        (
            len(pair["input"]),
            len(pair["input"][0]),
            len({cell for row in pair["input"] for cell in row}),
        )
        for pair in canonical_pairs(TASK_ID, root=ROOT)
    }
    total_hits = 0
    for band in ("easy", "medium", "hard"):
        hits = 0
        for index in range(20):
            seed = int(
                hashlib.sha256(
                    f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
                ).hexdigest()[:12],
                16,
            )
            sample_index = seed % 7919 + index
            grid = MODULE.generate(seed, sample_index, difficulty=band)
            profile = (
                len(grid),
                len(grid[0]),
                len({cell for row in grid for cell in row}),
            )
            hits += profile in profiles
        assert hits >= 1, f"{band} has no canonical-profile anchor"
        total_hits += hits
    assert total_hits >= 15, "canonical-envelope support is below the 25% floor"


def test_distributed_extrema_labels_match_registered_canonical_racket():
    import json

    from arc_repl.racket_bridge import RacketBridge

    record_path = (
        ROOT
        / "shared"
        / "data"
        / "base"
        / "solutions"
        / "training"
        / "1c02dbbe__3a4b67ab16ff.json"
    )
    program = json.loads(record_path.read_text())["racket_target"]["raw_code"]
    body = program.strip()[len("(rule!") : -1].strip()
    with RacketBridge(max_calls_before_restart=128) as bridge:
        for band_index, band in enumerate((None, "easy", "medium", "hard")):
            for seed in range(5):
                grid = MODULE.generate(
                    950_000 + band_index * 100 + seed,
                    seed * 47,
                    difficulty=band,
                    scene_profile="distributed_extrema",
                )
                bridge.define_grid("g", grid)
                assert bridge.eval_text(f"({body} g)") == MODULE.rule_mirror(grid)


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1"])
def test_generate_rejects_non_integer_seed(bad_seed):
    with pytest.raises(TypeError):
        MODULE.generate(bad_seed, 0)


@pytest.mark.parametrize("bad_index", [True, False, 1.0, 1.75, "1", -1])
def test_generate_rejects_invalid_sample_index(bad_index):
    with pytest.raises((TypeError, ValueError)):
        MODULE.generate(991, bad_index)
