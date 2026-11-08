"""Tests for the reusable evidence tool's independent pixel oracle."""
import copy
import importlib
import importlib.util
from pathlib import Path

import pytest

gen = importlib.import_module("puzzle_generators.per_puzzle.8b6543be4517.generator")
path = Path(gen.__file__).parent / "workspace/review_probe.py"
spec = importlib.util.spec_from_file_location("mirror_review_probe", path)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def test_independent_oracle_identifies_and_overwrites_collision():
    grid = probe.collision_witness()
    before = copy.deepcopy(grid)
    facts = probe.pixel_features(grid)
    assert facts["collisions"] == 1
    assert facts["additions"] == 2
    assert facts["axis"] == "col"
    assert probe.pixel_mirror(grid)[1][6] == 7
    assert probe.pixel_mirror(grid, zero_only=True)[1][6] == 5
    assert grid == before


@pytest.mark.parametrize("bad", [[], [[]], [[False]], [[10]], [[0], [1, 2]], None])
def test_independent_oracle_rejects_malformed_grids(bad):
    with pytest.raises(ValueError):
        probe.pixel_features(bad)


def test_html_escapes_case_names_and_shows_executed_labels(tmp_path):
    out = tmp_path / "witness.html"
    grid = probe.collision_witness()
    probe.write_witness_html(out, [{"name": "<script>bad</script>", "input": grid,
                                   "racket_output": probe.pixel_mirror(grid)}])
    text = out.read_text()
    assert "<script>bad</script>" not in text
    assert "&lt;script&gt;bad&lt;/script&gt;" in text
    assert "racket_output" in text


@pytest.mark.parametrize("transform", [probe.transpose, probe.flip_lr, probe.flip_ud])
def test_independent_oracle_is_dihedral_equivariant(transform):
    grid = probe.collision_witness()
    assert probe.pixel_mirror(transform(grid)) == transform(probe.pixel_mirror(grid))
