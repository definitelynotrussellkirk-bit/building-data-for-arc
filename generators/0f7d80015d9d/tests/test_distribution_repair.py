from __future__ import annotations

import copy
import hashlib
import importlib
import json
import os
import shutil
import subprocess
import sys

from reviewer_support import canonical_pairs, find_root


TASK_ID = "0f7d80015d9d"
gen = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)


def _analysis(grid):
    result = gen._analyze(grid)
    assert not result["errors"], result["errors"]
    return result


def test_canonical_anchor_blocks_put_both_markers_on_the_rectangle_cap_row():
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(8):
            anchor_count = 0
            for sample_index in range(32):
                if not gen._canonical_anchor(seed, sample_index):
                    continue
                anchor_count += 1
                grid = gen.generate(seed, sample_index, difficulty=difficulty)
                facts = _analysis(grid)
                cap_row = facts["rect"][0] - 1
                assert facts["red"][0] == cap_row
                assert facts["cyan"][0] == cap_row
            assert anchor_count == 8


def test_seed_phases_dealias_anchor_blocks_in_six_pair_episodes():
    counts = {
        sum(gen._canonical_anchor(seed, sample_index) for sample_index in range(6))
        for seed in range(128)
    }
    assert counts == {0, 2, 4}

    for seed in range(16):
        for block_start in range(0, 32, 4):
            decisions = {
                gen._canonical_anchor(seed, block_start + offset)
                for offset in range(4)
            }
            assert len(decisions) == 1


def test_strict_profile_rejects_canonical_geometry_with_noncanonical_marker_rows():
    pair = next(
        pair
        for pair in canonical_pairs(TASK_ID, root=find_root(__file__))
        if len(pair["input"]) == 9
    )
    grid = copy.deepcopy(pair["input"])
    facts = _analysis(grid)
    assert facts["red"][0] == facts["rect"][0] - 1
    assert facts["cyan"][0] == facts["rect"][0] - 1

    red_row, red_col = facts["red"]
    grid[red_row][red_col] = 7
    grid[0][red_col] = 2

    assert gen.self_check(grid) == []
    assert any(
        "immediately above" in reason
        for reason in gen.strict_canonical_like(grid)
    )


def test_generalized_hard_rectangles_include_thick_wide_and_tall_cases():
    wide_heights = set()
    tall_widths = set()
    for seed in range(96):
        wide = gen.generate(
            seed,
            7,
            difficulty="hard",
            grid_h=19,
            grid_w=19,
            rect_aspect="wide",
            scene_profile="left_opposite",
        )
        tall = gen.generate(
            seed,
            7,
            difficulty="hard",
            grid_h=19,
            grid_w=19,
            rect_aspect="tall",
            scene_profile="right_opposite",
        )
        wide_heights.add(_analysis(wide)["rect_h"])
        tall_widths.add(_analysis(tall)["rect_w"])

    assert max(wide_heights) >= 8
    assert max(tall_widths) >= 6


def test_rectangle_placement_supports_the_lawful_non_destination_edge():
    left_edge_seen = False
    right_edge_seen = False
    for seed in range(96):
        red_left = gen.generate(
            seed,
            9,
            grid_h=9,
            grid_w=9,
            rect_aspect="wide",
            scene_profile="left_opposite",
        )
        red_right = gen.generate(
            seed,
            9,
            grid_h=9,
            grid_w=9,
            rect_aspect="wide",
            scene_profile="right_opposite",
        )
        left_facts = _analysis(red_left)
        right_facts = _analysis(red_right)
        left_edge_seen |= left_facts["rect"][2] == 0
        right_edge_seen |= right_facts["rect"][3] == right_facts["width"] - 1

    assert left_edge_seen
    assert right_edge_seen


def test_declared_rivals_are_total_on_generated_edge_contact_scenes():
    edge_scenes = []
    for seed in range(128):
        for profile in gen.SCHEDULE_PROFILES:
            grid = gen.generate(
                seed,
                9,
                grid_h=9,
                grid_w=9,
                rect_aspect="wide",
                scene_profile=profile,
            )
            facts = _analysis(grid)
            if facts["rect"][2] == 0 or facts["rect"][3] == facts["width"] - 1:
                edge_scenes.append(grid)
        if len(edge_scenes) >= 8:
            break

    assert edge_scenes
    for grid in edge_scenes:
        for rival in gen.LESSON_COMPETITORS.values():
            prediction = rival(grid)
            assert len(prediction) == len(grid)
            assert all(len(row) == len(grid[0]) for row in prediction)

def test_distribution_probe_cli_bootstraps_the_packet_runtime(tmp_path):
    root = find_root(__file__)
    task_home = root / "generators" / TASK_ID
    if not task_home.is_dir():
        task_home = root / "puzzle_generators" / "per_puzzle" / TASK_ID
    script = task_home / "workspace" / "distribution_probe.py"
    generator = task_home / "generator.py"
    report = tmp_path / "probe.json"
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)

    completed = subprocess.run(
        [
            sys.executable,
            "-I",
            "-S",
            str(script),
            "--generator",
            str(generator),
            "--seeds",
            "2",
            "--episode-pairs",
            "2",
            "--schedule-indices",
            "8",
            "--out",
            str(report),
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(report.read_text())
    assert payload["generator_sha256"] == hashlib.sha256(generator.read_bytes()).hexdigest()


def test_distribution_probe_does_not_write_bytecode_beside_source(tmp_path):
    root = find_root(__file__)
    task_home = root / "generators" / TASK_ID
    if not task_home.is_dir():
        task_home = root / "puzzle_generators" / "per_puzzle" / TASK_ID
    script = task_home / "workspace" / "distribution_probe.py"
    copied_source = tmp_path / "source" / "generator.py"
    copied_source.parent.mkdir()
    shutil.copy2(task_home / "generator.py", copied_source)
    report = tmp_path / "probe.json"
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)

    completed = subprocess.run(
        [
            sys.executable,
            "-I",
            "-S",
            str(script),
            "--generator",
            str(copied_source),
            "--seeds",
            "1",
            "--episode-pairs",
            "1",
            "--schedule-indices",
            "4",
            "--out",
            str(report),
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert completed.returncode == 0, completed.stderr
    assert not (copied_source.parent / "__pycache__").exists()
