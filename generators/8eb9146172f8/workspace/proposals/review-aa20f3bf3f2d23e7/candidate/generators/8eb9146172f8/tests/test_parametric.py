from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_ROOT = REPO_ROOT / "shared/runtime"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

PROTOTYPE_PATH = (
    REPO_ROOT / "generators/8eb9146172f8/workspace/parametric/prototype.py"
)


def _load_prototype():
    assert PROTOTYPE_PATH.is_file(), "parametric prototype has not been implemented"
    spec = importlib.util.spec_from_file_location(
        "review_8eb9146172f8_parametric", PROTOTYPE_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _witness_grid() -> list[list[int]]:
    grid = [[0] * 9 for _ in range(9)]
    grid[4][0] = 8
    grid[0][3] = 2
    grid[0][6] = 2
    return grid


def _cells(grid: list[list[int]], color: int) -> set[tuple[int, int]]:
    return {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    }


def test_rule_family_preserves_exact_canonical_default_and_rejects_invalid_settings():
    prototype = _load_prototype()

    canonical = prototype.canonical_rule()
    assert prototype.emit_rule(1) == canonical
    assert prototype.emit_rule(2) != canonical

    for invalid in (True, False, 0, 3, -1, 1.0, "1", None):
        with pytest.raises(ValueError, match="step_size"):
            prototype.emit_rule(invalid)
        with pytest.raises(ValueError, match="step_size"):
            prototype.apply_python(_witness_grid(), invalid)


def test_python_mirror_has_hand_derived_step_one_and_step_two_paths():
    prototype = _load_prototype()
    grid = _witness_grid()

    step_one = prototype.apply_python(grid, 1)
    step_two = prototype.apply_python(grid, 2)

    assert _cells(step_one, 2) == {(0, 3), (0, 6)}
    assert _cells(step_two, 2) == {(0, 3), (0, 6)}
    assert _cells(step_one, 8) == {
        (4, 0), (4, 1), (4, 2),
        (5, 3), (5, 4), (5, 5),
        (6, 6), (6, 7), (6, 8),
    }
    assert _cells(step_two, 8) == {
        (4, 0), (4, 1), (4, 2),
        (6, 3), (6, 4), (6, 5),
        (8, 6), (8, 7), (8, 8),
    }
    assert grid == _witness_grid(), "the mirror must not mutate its input"


def test_racket_is_label_authority_and_matches_python_for_both_settings():
    prototype = _load_prototype()
    grid = _witness_grid()

    with prototype.open_verifier() as verifier:
        for step_size in prototype.STEP_SIZES:
            source = prototype.emit_rule(step_size)
            racket = verifier.apply(source, grid)
            assert racket == prototype.apply_python(grid, step_size)


def _episode_input_hashes(episode) -> list[str]:
    return [pair["input_sha256"] for pair in [*episode["train"], *episode["test"]]]


def test_episode_is_fixed_identifiable_from_demos_and_has_four_distinct_queries():
    prototype = _load_prototype()

    for step_size in prototype.STEP_SIZES:
        episode = prototype.make_episode(
            1729, step_size=step_size, n_train=4, n_test=4
        )
        pairs = [*episode["train"], *episode["test"]]

        assert episode["parameters"] == {"step_size": step_size}
        assert episode["n_train"] == 4
        assert episode["n_test"] == 4
        assert len(pairs) == 8
        assert len(set(_episode_input_hashes(episode))) == 8
        assert episode["analysis"]["identified_from_demonstrations"] is True
        assert episode["analysis"]["surviving_step_sizes_after_demos"] == [step_size]
        assert len(episode["analysis"]["demo_refutation_indices"]) == 4
        assert len(episode["analysis"]["queries"]) == 4
        assert all(row["rival_differs"] for row in episode["analysis"]["queries"])
        assert episode["verification"]["racket_python_parity_count"] == 16
        assert all(pair["step_size"] == step_size for pair in pairs)


def test_seeded_parameter_and_input_prefix_do_not_depend_on_requested_query_count():
    prototype = _load_prototype()

    first = prototype.make_episode(5, n_train=4, n_test=4)
    repeated = prototype.make_episode(5, n_train=4, n_test=4)
    extended = prototype.make_episode(5, n_train=4, n_test=5)

    assert first["parameters"] == {"step_size": 2}
    assert first["parameters"] == repeated["parameters"] == extended["parameters"]
    assert _episode_input_hashes(first) == _episode_input_hashes(repeated)
    assert _episode_input_hashes(first) == _episode_input_hashes(extended)[:8]
    assert first["train"] == repeated["train"]
    assert first["test"] == repeated["test"]


def test_materialized_public_files_are_visible_only_content_addressed_and_private_mapped(
    tmp_path,
):
    import hashlib
    import json

    prototype = _load_prototype()
    out = tmp_path / "evidence"
    report = prototype.materialize(
        seed=2468,
        step_size=None,
        all_settings=True,
        n_train=4,
        n_test=4,
        out=out,
    )

    public_files = sorted((out / "public").glob("challenge-*.json"))
    private_files = sorted((out / "private").glob("episode-*.json"))
    assert len(public_files) == len(private_files) == 2
    assert report["episode_count"] == 2
    assert report["cross_setting_same_inputs"] is True
    assert report["cross_setting_outputs_differ"] is True

    public_ids = set()
    for path in public_files:
        raw = path.read_bytes()
        public_id = path.stem.removeprefix("challenge-")
        public_ids.add(public_id)
        assert len(public_id) == 64
        assert hashlib.sha256(raw).hexdigest() == public_id
        assert b'"step_size"' not in raw
        assert b'"seed"' not in raw
        assert b'"racket"' not in raw.lower()
        visible = json.loads(raw)
        assert set(visible) == {"train", "test"}
        assert all(set(pair) == {"input", "output"} for pair in visible["train"])
        assert all(set(pair) == {"input"} for pair in visible["test"])
        assert len(visible["train"]) == len(visible["test"]) == 4

    for path in private_files:
        private = json.loads(path.read_text())
        assert private["public_id"] in public_ids
        assert private["parameters"]["step_size"] in prototype.STEP_SIZES
        assert all("output" in pair for pair in private["test"])
        assert private["racket_source"]
        assert private["racket_sha256"]


def test_public_projection_ignores_private_metadata_and_hidden_query_outputs():
    import copy

    prototype = _load_prototype()
    episode = prototype.make_episode(101, step_size=1, n_train=4, n_test=4)
    original_bytes = prototype.visible_bytes(episode)
    original_id = prototype.visible_id(episode)

    changed = copy.deepcopy(episode)
    changed["seed"] = 999999
    changed["parameters"]["step_size"] = 2
    changed["test"][0]["output"][0][0] = (
        changed["test"][0]["output"][0][0] + 1
    ) % 10
    changed["analysis"] = {"invented_private_note": "does not affect visibility"}

    assert prototype.visible_bytes(changed) == original_bytes
    assert prototype.visible_id(changed) == original_id


def test_invalid_episode_and_materialization_arguments_fail_loudly(tmp_path):
    prototype = _load_prototype()

    for seed in (True, -1, 1.5, "7", None):
        with pytest.raises(ValueError, match="seed"):
            prototype.make_episode(seed)
    for count in (True, 0, 33, 1.5, "4", None):
        with pytest.raises(ValueError, match="n_train"):
            prototype.make_episode(1, n_train=count)
        with pytest.raises(ValueError, match="n_test"):
            prototype.make_episode(1, n_test=count)
    for step_size in (True, 0, 3, 1.0, "2"):
        with pytest.raises(ValueError, match="step_size"):
            prototype.make_episode(1, step_size=step_size)
    with pytest.raises(ValueError, match="all_settings"):
        prototype.materialize(
            seed=1,
            step_size=1,
            all_settings=True,
            n_train=4,
            n_test=4,
            out=tmp_path / "bad",
        )


def test_materialized_batches_are_sorted_by_opaque_public_id(tmp_path):
    import json

    prototype = _load_prototype()
    out = tmp_path / "sorted-evidence"
    report = prototype.materialize(
        seed=4,
        step_size=None,
        all_settings=True,
        n_train=4,
        n_test=4,
        out=out,
    )

    private_ids = [
        json.loads(path.read_text())["public_id"]
        for path in sorted((out / "private").glob("episode-*.json"))
    ]
    assert report["public_ids"] == sorted(report["public_ids"])
    assert private_ids == report["public_ids"]


def test_materialized_rule_file_names_hash_exact_rule_bytes(tmp_path):
    import hashlib

    prototype = _load_prototype()
    out = tmp_path / "exact-rule-evidence"
    prototype.materialize(
        seed=2468,
        step_size=None,
        all_settings=True,
        n_train=4,
        n_test=4,
        out=out,
    )

    rules = sorted((out / "private/rules").glob("rule-*.rkt"))
    assert len(rules) == 2
    for path in rules:
        expected = path.stem.removeprefix("rule-")
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
