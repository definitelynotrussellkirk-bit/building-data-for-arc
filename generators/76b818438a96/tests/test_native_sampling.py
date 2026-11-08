"""Regressions for native path lessons: safe rays, scale, teaching and export."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]


def load_prototype():
    path = HOME / "workspace/parametric/prototype.py"
    spec = importlib.util.spec_from_file_location("_path_native_sampling_prototype", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_native_sampler_exists_and_uses_independent_query_stream():
    module = load_prototype()
    assert callable(getattr(module, "sample_inputs", None)), "native input sampler is missing"
    demos, queries, receipt = module.sample_inputs(17, 3, 4)
    short_demos, short_queries, _ = module.sample_inputs(17, 3, 1)
    assert demos == short_demos
    assert queries[:1] == short_queries
    assert len({json.dumps(g) for g in demos + queries}) == 7
    assert receipt["rejected_candidates"] >= 0


def test_stress_draw_is_large_content_not_padded_small_scene():
    module = load_prototype()
    assert callable(getattr(module, "sample_inputs", None)), "native input sampler is missing"
    demos, queries, _ = module.sample_inputs(17, 2, 4)
    for grid in (demos[1], queries[3]):
        assert len(grid) == len(grid[0]) == 30
        cells = [(r, c) for r, row in enumerate(grid) for c, color in enumerate(row) if color]
        assert len(cells) >= 60
        assert min(r for r, _ in cells) == min(c for _, c in cells) == 0
        assert max(r for r, _ in cells) == max(c for _, c in cells) == 29


def test_native_geometry_rejects_obscured_extra_marker_ray():
    module = load_prototype()
    assert callable(getattr(module, "scene_issues", None)), "native ray safety check is missing"
    generator = module.load_generator()
    grid = generator.generate(987076, 76, difficulty="hard")
    assert not generator.self_check(grid)
    assert any("ray" in reason for reason in module.scene_issues(grid))


@pytest.mark.parametrize("demos,queries", [(1, 4), (7, 4), (3, 0), (3, 5), (True, 4), (3, 1.0)])
def test_native_count_limits_fail_before_execution(demos, queries):
    module = load_prototype()
    with pytest.raises((TypeError, ValueError)):
        module.build_episode(seed=1, parameter="opposite", n_train=demos, n_test=queries)


def test_writer_hashes_visible_bytes_and_refuses_existing_destination(tmp_path):
    module = load_prototype()
    from reviewer_support import public_challenge_bytes, public_challenge_id
    challenge = {"train": [{"input": [[0]], "output": [[1]]}], "test": [{"input": [[2]]}]}
    episode = {"schema": "test", "seed": 7, "parameter": "opposite", "public_challenge": challenge,
               "test": [{"selected_output": [[3]]}]}
    paths = module.write_episode(episode, tmp_path / "export")
    public_path = Path(paths["challenge"])
    assert public_path.name == public_challenge_id(challenge) + ".json"
    assert public_path.read_bytes() == public_challenge_bytes(challenge)
    assert set(json.loads(public_path.read_text())) == {"train", "test"}
    with pytest.raises(FileExistsError):
        module.write_episode(episode, tmp_path / "export")


def test_sampler_exhaustion_is_bounded_and_visible(monkeypatch):
    module = load_prototype()
    checked = []

    def reject(grid):
        checked.append(grid)
        return ["forced invalid geometry"]

    monkeypatch.setattr(module, "scene_issues", reject)
    with pytest.raises(RuntimeError, match="exhausted 32 attempts"):
        module.sample_inputs(17, 2, 4)
    assert len(checked) == 32


def test_private_metadata_cannot_change_public_bytes_or_identifier(tmp_path):
    from copy import deepcopy
    module = load_prototype()
    challenge = {"train": [{"input": [[0]], "output": [[1]]}], "test": [{"input": [[2]]}]}
    first = {"schema": "test", "seed": 7, "parameter": "opposite", "public_challenge": challenge,
             "test": [{"selected_output": [[3]]}], "programs": {"private": "first"}}
    second = deepcopy(first)
    second.update(seed=999, parameter="aligned", programs={"private": "different"})
    second["test"][0]["selected_output"] = [[9]]
    left = Path(module.write_episode(first, tmp_path / "a")["challenge"])
    right = Path(module.write_episode(second, tmp_path / "b")["challenge"])
    assert left.name == right.name
    assert left.read_bytes() == right.read_bytes()


def test_teaching_guard_detects_racket_backed_cap_shortcut():
    module = load_prototype()
    inputs = [module._scaled_scene(seed, 14, teaching=True) for seed in (1, 2)]
    inputs.append(module._scaled_scene(3, 30, teaching=True))
    correct = module.load_programs()["opposite"]
    capped = correct.replace("(ext-count (length ext-cells))", "(ext-count (min 6 (length ext-cells)))")
    outputs, identity = module.execute_programs(inputs, [correct, capped])
    assert identity["backend"] == "racket" and identity["protected"] is True
    assert outputs[0][:2] == outputs[1][:2]
    assert outputs[0][2] != outputs[1][2]
    pairs = [{"input": grid, "output": output} for grid, output in zip(inputs, outputs[0])]
    rejected = module.teaching_check(pairs[:2], pairs[2:], "opposite")
    assert "cap_6" in rejected["unsafe_rivals"]
    # The constructive large demonstration repairs the ambiguity at the same count.
    repaired = module.teaching_check([pairs[0], pairs[2]], [pairs[1]], "opposite")
    assert repaired["unsafe_rivals"] == []
