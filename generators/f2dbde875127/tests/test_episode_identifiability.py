"""Episode-level teaching and cross-band distribution regressions."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
sys.path.insert(0, str(REPO / "shared/runtime"))
sys.path.insert(0, str(HOME / "workspace"))


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


gen = _load("episode_review_f2dbde875127", HOME / "generator.py")
probe = _load("episode_key_probe", HOME / "workspace/key_contrast_probe.py")
gate = _load("episode_lesson_gate", HOME / "workspace/lesson_key_gate.py")


def _first_key(grid) -> int:
    return probe.frame_records(grid)[0]["key_cell"][2]


def _is_centered(record) -> bool:
    r0, c0, r1, c1 = record["box"]
    points = record["points"]
    lo_r = min(r for r, _ in points)
    lo_c = min(c for _, c in points)
    obj_h = max(r for r, _ in points) - lo_r + 1
    obj_w = max(c for _, c in points) - lo_c + 1
    interior_h = r1 - r0 - 1
    interior_w = c1 - c0 - 1
    target = (r0 + 1 + (interior_h - obj_h) // 2,
              c0 + 1 + (interior_w - obj_w) // 2)
    return (lo_r, lo_c) == target


def test_four_visible_examples_cover_every_first_frame_key():
    assert gen.EXAMPLES_NEEDED == 4
    for seed in range(16):
        for start in range(4):
            keys = [_first_key(gen.generate(seed, start + offset, difficulty="medium"))
                    for offset in range(gen.EXAMPLES_NEEDED)]
            assert set(keys) == {2, 3, 4, 5}, (seed, start, keys)


def test_four_demo_lessons_identify_every_query_key_under_declared_rivals():
    for seed in range(32):
        pairs = []
        for sample_index in range(gen.EXAMPLES_NEEDED + 2):
            grid = gen.generate(seed, sample_index, difficulty="medium")
            pairs.append({"input": grid, "output": probe.python_transform(grid)})
        lesson = {
            "train": pairs[:gen.EXAMPLES_NEEDED],
            "test": [{"input": pair["input"]} for pair in pairs[gen.EXAMPLES_NEEDED:]],
        }
        report = gate.analyze_lesson(lesson)
        assert report["passed"], (seed, report["ambiguous_query_keys"], report["errors"],
                                  report["observed_key_frames"])


def test_default_difficulty_bands_do_not_replay_identical_inputs():
    for seed in range(32):
        grids = [gen.generate(seed, 0, difficulty=band)
                 for band in ("easy", "medium", "hard")]
        assert len({repr(grid) for grid in grids}) == 3, seed


def test_every_ordinary_object_starts_off_center():
    for band in ("easy", "medium", "hard"):
        for seed in range(32):
            for record in probe.frame_records(gen.generate(seed, 0, difficulty=band)):
                assert not _is_centered(record), (band, seed, record["box"], record["key_cell"])


def test_episode_probe_exposes_only_public_query_inputs():
    tool_path = HOME / "workspace/episode_identifiability_probe.py"
    assert tool_path.is_file(), "missing reusable actual-episode identifiability probe"
    tool = _load("episode_identifiability_probe_under_test", tool_path)
    episode = {
        "train": [{"input": [[0]], "output": [[1]]}],
        "test": [{"input": [[2]], "output": [[9]]}],
    }
    public = tool.public_lesson(episode)
    assert public == {
        "train": [{"input": [[0]], "output": [[1]]}],
        "test": [{"input": [[2]]}],
    }
    public["test"][0]["input"][0][0] = 7
    assert episode["test"][0]["input"] == [[2]]


def test_episode_probe_reads_example_contract_without_runtime_imports():
    import os
    import subprocess

    script = (
        "import importlib.util; from pathlib import Path; "
        "p=Path('generators/f2dbde875127/workspace/episode_identifiability_probe.py'); "
        "s=importlib.util.spec_from_file_location('portable_episode_probe',p); "
        "m=importlib.util.module_from_spec(s); s.loader.exec_module(m); "
        "print(m._generator_examples_needed())"
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = "src"
    run = subprocess.run([sys.executable, "-E", "-s", "-c", script], cwd=REPO,
                         env=env, text=True, capture_output=True)
    assert run.returncode == 0, run.stderr
    assert run.stdout.strip() == "4"


def test_distribution_probe_runs_standalone_without_pythonpath(tmp_path):
    import os
    import subprocess

    tool_path = HOME / "workspace/distribution_contract_probe.py"
    out_path = tmp_path / "distribution.json"
    env = {key: value for key, value in os.environ.items()
           if not key.startswith("PYTHON")}
    run = subprocess.run(
        [sys.executable, "-E", "-s", str(tool_path),
         "--count", "1", "--out", str(out_path)],
        cwd=REPO, env=env, text=True, capture_output=True,
    )
    assert run.returncode == 0, run.stderr
    assert out_path.is_file()


def test_distribution_probe_binds_cross_band_and_teaching_invariants():
    tool_path = HOME / "workspace/distribution_contract_probe.py"
    assert tool_path.is_file(), "missing reusable distribution-contract probe"
    tool = _load("distribution_contract_probe_under_test", tool_path)
    report = tool.analyze(start_seed=0, count=8, sample_index=0)
    assert report["source_bound"]
    assert report["counts"]["cross_band_duplicate_seed_count"] == 0
    assert report["counts"]["off_center_violations"] == 0
    assert report["counts"]["four_sample_key_windows_failed"] == 0
    assert report["passed"]


def test_distribution_probe_accepts_an_explicit_source_snapshot():
    tool = _load(
        "distribution_contract_explicit_source_under_test",
        HOME / "workspace/distribution_contract_probe.py",
    )
    report = tool.analyze(
        start_seed=0,
        count=2,
        sample_index=0,
        generator_path=HOME / "generator.py",
    )
    assert report["source_path"] == str((HOME / "generator.py").resolve())
    assert report["source_bound"]
