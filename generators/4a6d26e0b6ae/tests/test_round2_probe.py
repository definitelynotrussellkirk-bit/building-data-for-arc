"""The integrity CLI must not turn validation failures into green summaries."""
import importlib.util
import json
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]


def probe():
    spec = importlib.util.spec_from_file_location("round2_integrity_probe", HOME / "workspace/verify_distribution.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def grid():
    result = [[0]*9 for _ in range(7)]
    result[1][1] = result[1][3] = 4
    result[3][5] = result[5][5] = 7
    return result


def fake_source(tmp_path, *, reject=False, recorded_count=False):
    path = tmp_path / "source.py"
    body = ""
    if recorded_count:
        body = '''\n    from puzzle_generators.base import gen_ctx\n    ctx=gen_ctx(seed=seed, sample_index=sample_index, task_id=TASK_ID, version=VERSION, overrides={})\n    ctx.draw_int("gap_count", 2, 2)\n'''
    path.write_text('TASK_ID="4a6d26e0b6ae"\nVERSION="test-fixture"\n'
        'def generate(seed, sample_index, *, difficulty=None, **overrides):\n'
        + body + f'    return {grid()!r}\n'
        + f'def self_check(grid, **kwargs):\n    return {["injected selfcheck rejection"] if reject else []!r}\n')
    return path


def run(p, source, out, extra=()):
    return p.main(["--repo", str(ROOT), "--source", str(source), "--seeds", "1", "--out", str(out), *extra])


def test_selfcheck_rejection_is_a_failed_draw_and_retains_witness(tmp_path):
    p = probe(); source = fake_source(tmp_path, reject=True); out = tmp_path / "evidence"
    assert run(p, source, out) == 1
    summary = json.loads((out / "summary.json").read_text())
    assert not summary["passed"]
    assert summary["counters"]["selfcheck_rejected_draws"] == 1
    row = json.loads((out / "failures.jsonl").read_text())
    assert row["input"] == grid()
    assert row["self_check"] == ["injected selfcheck rejection"]


def test_explicit_requested_count_beats_conflicting_drawn_metadata(tmp_path):
    p = probe(); source = fake_source(tmp_path, recorded_count=True); out = tmp_path / "evidence"
    assert run(p, source, out, ["--override", "gap_count=3"]) == 1
    row = json.loads((out / "failures.jsonl").read_text())
    assert row["inspection"]["count_mismatch"]


@pytest.mark.parametrize("override", ["grid_h=14", "grid_w=5", 'texture="horizontal"', 'texture="edge"', "colors=[1,2]"])
def test_independent_probe_detects_ignored_noncount_controls(tmp_path, override):
    assert run(probe(), fake_source(tmp_path), tmp_path / "evidence", ["--override", override]) == 1


def test_probe_does_not_overwrite_previous_evidence(tmp_path):
    p = probe(); source = fake_source(tmp_path); out = tmp_path / "evidence"
    assert run(p, source, out) == 0
    before = {f.name: f.read_bytes() for f in out.iterdir()}
    with pytest.raises((FileExistsError, SystemExit)):
        run(p, source, out)
    assert before == {f.name: f.read_bytes() for f in out.iterdir()}


def test_probe_rejects_out_of_domain_dimensions():
    assert probe().inspect_scene([[1, 0, 1]], expected_count=1)["issues"]


def test_duplicate_override_keys_do_not_silently_discard_a_request(tmp_path):
    with pytest.raises(SystemExit):
        run(probe(), fake_source(tmp_path), tmp_path / "evidence", ["--override", "grid_h=7", "--override", "grid_h=14"])
