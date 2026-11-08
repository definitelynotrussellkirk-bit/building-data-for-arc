"""Regressions for prototype counts and visible-content public exports.

These checks apply only to the isolated boundary-palette prototype. Canonical
generator approval and production dataset identities are outside their scope.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import (
    find_root,
    public_challenge_bytes,
    public_challenge_id,
)


PROTOTYPE_PATH = (
    Path(__file__).resolve().parents[1] / "workspace" / "parametric" / "prototype.py"
)
ROOT = find_root(__file__)


def _load():
    assert PROTOTYPE_PATH.exists(), "boundary-palette prototype has not been implemented"
    spec = importlib.util.spec_from_file_location(
        "boundary_palette_export_prototype", PROTOTYPE_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _input_key(pair):
    return json.dumps(pair["input"], separators=(",", ":"))


def _public_fixture(color=1):
    return {
        "schema": "arcpuzzles-parametric-boundary-palette-public-v1",
        "train": [{"input": [[5, 5]], "output": [[color, color]]}],
        "test": [{"input": [[0, 5, 0]]}],
    }


class _IntegerSubclass(int):
    pass


@pytest.mark.parametrize("count_name", ["n_train", "n_test"])
@pytest.mark.parametrize("bad_count", [True, False, 1.0, "2", None, _IntegerSubclass(2)])
def test_counts_require_literal_integers(count_name, bad_count, monkeypatch):
    prototype = _load()
    def unexpected_execution(*args, **kwargs):
        pytest.fail("invalid counts must be rejected before Racket execution")
    monkeypatch.setattr(prototype, "_racket_outputs", unexpected_execution)
    with pytest.raises(TypeError, match=count_name):
        prototype.build_episode(root=ROOT, seed=18, **{count_name: bad_count})


@pytest.mark.parametrize("count_name", ["n_train", "n_test"])
@pytest.mark.parametrize("bad_count", [0, -1, 33])
def test_counts_must_be_within_supported_positive_range(
    count_name, bad_count, monkeypatch
):
    prototype = _load()
    def unexpected_execution(*args, **kwargs):
        pytest.fail("invalid counts must be rejected before Racket execution")
    monkeypatch.setattr(prototype, "_racket_outputs", unexpected_execution)
    with pytest.raises(ValueError, match=count_name):
        prototype.build_episode(root=ROOT, seed=18, **{count_name: bad_count})


def test_default_episode_has_four_demonstrations_and_four_distinct_queries():
    prototype = _load()
    episode = prototype.build_episode(root=ROOT, seed=18)
    assert len(episode["train"]) == len(episode["test"]) == 4
    keys = [_input_key(pair) for pair in [*episode["train"], *episode["test"]]]
    assert len(set(keys)) == 8


@pytest.mark.parametrize("seed,n_train,n_test", [(18, 1, 3), (19, 6, 5)])
def test_counts_are_independent_and_all_requested_inputs_are_distinct(
    seed, n_train, n_test
):
    prototype = _load()
    episode = prototype.build_episode(
        root=ROOT, seed=seed, n_train=n_train, n_test=n_test
    )
    assert len(episode["train"]) == n_train
    assert len(episode["test"]) == n_test
    assert episode["parameter"] == {
        "boundary_palette": prototype.choose_boundary_palette(seed)
    }
    pairs = [*episode["train"], *episode["test"]]
    assert len({_input_key(pair) for pair in pairs}) == n_train + n_test
    assert all("output" in pair for pair in pairs)


def test_changing_query_count_preserves_demonstrations_and_query_prefix():
    prototype = _load()
    short = prototype.build_episode(root=ROOT, seed=19, n_train=3, n_test=1)
    long = prototype.build_episode(root=ROOT, seed=19, n_train=3, n_test=5)
    assert short["train"] == long["train"]
    assert short["test"] == long["test"][:1]
    assert short["parameter"] == long["parameter"]


def test_duplicate_exhaustion_is_bounded_and_never_returns_a_partial_episode(monkeypatch):
    prototype = _load()
    module, path, source_sha = prototype.load_selected_generator(prototype.TASK_ID, root=ROOT)
    attempts = []

    def repeated_input(seed, index, **kwargs):
        attempts.append(index)
        return [[0, 0, 0], [0, 5, 0], [0, 0, 0]]

    def unexpected_execution(*args, **kwargs):
        pytest.fail("incomplete episodes must fail before reference execution")

    monkeypatch.setattr(module, "generate", repeated_input)
    monkeypatch.setattr(prototype, "load_selected_generator", lambda *args, **kwargs: (module, path, source_sha))
    monkeypatch.setattr(prototype, "_racket_outputs", unexpected_execution)
    with pytest.raises(RuntimeError, match="distinct inputs"):
        prototype.build_episode(root=ROOT, seed=18, n_train=2, n_test=4)
    assert attempts == list(range(64))


def test_episode_propagates_reference_execution_failure_without_python_fallback(
    monkeypatch,
):
    prototype = _load()

    def failed_reference_execution(*args, **kwargs):
        raise RuntimeError("sentinel reference execution failure")

    monkeypatch.setattr(prototype, "_racket_outputs", failed_reference_execution)
    with pytest.raises(RuntimeError, match="sentinel reference execution failure"):
        prototype.build_episode(root=ROOT, seed=18, n_train=1, n_test=1)


def test_cli_rejects_private_report_inside_public_directory_before_work(
    tmp_path, monkeypatch, capsys
):
    prototype = _load()
    public_dir = tmp_path / "public"
    report_path = public_dir / "nested" / "private-report.json"

    def unexpected_generation(*args, **kwargs):
        pytest.fail("unsafe export paths must be rejected before generating labels")

    monkeypatch.setattr(prototype, "build_report", unexpected_generation)
    monkeypatch.setattr(prototype, "materialize_rules", unexpected_generation)
    monkeypatch.setattr(prototype, "find_root", lambda *args: ROOT)
    monkeypatch.setattr(
        sys,
        "argv",
        [str(PROTOTYPE_PATH), "--out", str(report_path),
         "--write-public", str(public_dir)],
    )
    with pytest.raises(SystemExit) as error:
        prototype.main()
    assert error.value.code == 2
    assert "error:" in capsys.readouterr().err
    assert not public_dir.exists()
    assert not report_path.exists()


def test_public_projection_strips_all_pair_and_episode_private_metadata():
    prototype = _load()
    episode = {
        "seed": 19,
        "parameter": {"boundary_palette": "ends4_edges1"},
        "mode": "ends4_edges1",
        "program": "(rule! private-reference)",
        "train": [{
            "input": [[5]], "output": [[4]],
            "scene_profile": "private-training-profile", "sample_index": 12,
        }],
        "test": [{
            "input": [[5, 5]], "output": [[4, 4]],
            "scene_profile": "private-query-profile", "sample_index": 13,
        }],
    }
    public = prototype.public_challenge(episode)
    assert set(public) <= {"schema", "train", "test"}
    assert public["train"] == [{"input": [[5]], "output": [[4]]}]
    assert public["test"] == [{"input": [[5, 5]]}]
    # A downstream editor must not be able to mutate the private episode.
    public["train"][0]["output"][0][0] = 9
    public["test"][0]["input"][0][0] = 0
    assert episode["train"][0]["output"] == [[4]]
    assert episode["test"][0]["input"] == [[5, 5]]


def test_writer_uses_exact_shared_visible_bytes_and_sorted_content_ids(tmp_path):
    prototype = _load()
    challenges = [_public_fixture(color) for color in (1, 4, 2)]
    original = copy.deepcopy(challenges)
    expected = sorted(
        [{"public_id": public_challenge_id(challenge),
          "filename": f"{public_challenge_id(challenge)}.json"}
         for challenge in challenges],
        key=lambda row: row["public_id"],
    )
    out = tmp_path / "public"
    rows = prototype.write_public_challenges(iter(reversed(challenges)), out=out)
    assert rows == expected
    assert sorted(path.name for path in out.iterdir()) == sorted(
        row["filename"] for row in expected
    )
    by_id = {public_challenge_id(challenge): challenge for challenge in challenges}
    for row in rows:
        payload = (out / row["filename"]).read_bytes()
        assert payload == public_challenge_bytes(by_id[row["public_id"]])
        assert hashlib.sha256(payload).hexdigest() == row["public_id"]
        assert set(json.loads(payload)) == {"train", "test"}
    assert challenges == original


def test_private_metadata_and_query_answers_cannot_change_export_identity(tmp_path):
    prototype = _load()
    visible = _public_fixture()
    private = copy.deepcopy(visible)
    private.update({
        "seed": 987654, "parameter": {"boundary_palette": "ends4_edges1"},
        "mode": "ends4_edges1", "program": "private-reference",
    })
    private["train"][0]["sample_index"] = 42
    private["test"][0].update({"output": [[9, 9, 9]], "sample_index": 99})
    first = prototype.write_public_challenges([visible], out=tmp_path / "first")
    second = prototype.write_public_challenges([private], out=tmp_path / "second")
    assert first == second
    name = first[0]["filename"]
    assert (tmp_path / "first" / name).read_bytes() == (
        tmp_path / "second" / name
    ).read_bytes() == public_challenge_bytes(visible)


def test_duplicate_visible_payloads_are_rejected_before_writing(tmp_path):
    prototype = _load()
    first = _public_fixture()
    duplicate = copy.deepcopy(first)
    duplicate["seed"] = 19
    duplicate["test"][0]["output"] = [[4, 4, 4]]
    out = tmp_path / "public"
    with pytest.raises(ValueError, match="(?i)duplicate"):
        prototype.write_public_challenges([first, duplicate], out=out)
    assert not out.exists() or not list(out.iterdir())


def test_existing_destination_refuses_whole_batch_without_partial_exports(tmp_path):
    prototype = _load()
    challenges = sorted(
        [_public_fixture(1), _public_fixture(4)], key=public_challenge_id
    )
    out = tmp_path / "public"
    out.mkdir()
    # Make the later target collide, so checking only immediately before each
    # write would incorrectly leave an earlier new public file behind.
    existing = out / f"{public_challenge_id(challenges[-1])}.json"
    sentinel = b"preserve the existing destination exactly\n"
    existing.write_bytes(sentinel)
    with pytest.raises(FileExistsError):
        prototype.write_public_challenges(challenges, out=out)
    assert existing.read_bytes() == sentinel
    assert list(out.iterdir()) == [existing]
